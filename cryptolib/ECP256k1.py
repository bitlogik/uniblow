# -*- coding: utf8 -*-

# SECP_256k1 curve points computation library
# Copyright (C) 2014  Antoine FERRON
# Copyright (C) 2021  BitLogiK

# Some portions based on :
# "python-ecdsa" Copyright (C) 2010 Brian Warner (MIT Licence)
# "Simple Python elliptic curves and ECDSA" Copyright (C) 2005 Peter Pearson (public domain)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

# secp256k1
_p = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_r = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_b = 0x0000000000000000000000000000000000000000000000000000000000000007
# a = 0x00
_Gx = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
_Gy = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8


class ECPoint:
    def __init__(self, x, y):
        self.__x = x
        self.__y = y

    def __eq__(self, other):
        if self.__x == other.__x and self.__y == other.__y:
            return True
        else:
            return False

    def __add__(self, other):
        if other == INFINITY:
            return self
        if self == INFINITY:
            return other
        if self.__x == other.__x:
            if (self.__y + other.__y) % _p == 0:
                return INFINITY
            else:
                return self.double()
        slope = ((other.__y - self.__y) * inverse_mod(other.__x - self.__x, _p)) % _p
        x3 = (slope * slope - self.__x - other.__x) % _p
        return ECPoint(x3, (slope * (self.__x - x3) - self.__y) % _p)

    def __mul__(self, e):
        if e >= _r:
            e = e % _r
        if e == 0:
            return INFINITY
        if self == INFINITY:
            return INFINITY
        e3 = 3 * e
        negative_self = ECPoint(self.__x, -self.__y)
        i = 0x100000000000000000000000000000000000000000000000000000000000000000
        while i > e3:
            i >>= 1
        result = self
        while i > 2:
            i >>= 1
            result = result.double()
            ei = e & i
            if (e3 & i) ^ ei:
                if ei == 0:
                    result += self
                else:
                    result += negative_self
        return result

    def __rmul__(self, other):
        return self * other

    def __str__(self):
        if self == INFINITY:
            return "infinity"
        return "(%d,%d)" % (self.__x, self.__y)

    def double(self):
        if self == INFINITY:
            return INFINITY
        xyd = ((self.__x * self.__x) * inverse_mod(2 * self.__y, _p)) % _p
        x3 = (9 * xyd * xyd - 2 * self.__x) % _p
        return ECPoint(x3, (3 * xyd * (self.__x - x3) - self.__y) % _p)

    def dual_mult(self, k1, k2):
        # Compute k1.G+k2.self
        if k2 >= _r:
            k2 = k2 % _r
        if k2 == 0:
            return INFINITY
        if self == INFINITY:
            return INFINITY
        if k1 == 0:
            return INFINITY
        assert k2 > 0
        assert k1 > 0
        e3, k3 = 3 * k2, 3 * k1
        negative_self = self.negate()
        i = 0x100000000000000000000000000000000000000000000000000000000000000000
        ke3 = e3 | k3
        while i > ke3:
            i >>= 1
        if k3 > e3:
            result = generator_256
            if (e3 & i) == (k3 & i):
                result += self
        else:
            result = self
            if (e3 & i) == (k3 & i):
                result += generator_256
        while i > 2:
            i >>= 1
            result = result.double()
            ei, ki = k2 & i, k1 & i
            if (e3 & i) ^ ei:
                if ei == 0:
                    result += self
                else:
                    result += negative_self
            if (k3 & i) ^ ki:
                if ki == 0:
                    result += generator_256
                else:
                    result += neg_generator_256
        return result

    def negate(self):
        """Retrun the symetric sister point"""
        return ECPoint(self.__x, -self.__y % _p)

    def x(self):
        return self.__x

    def y(self):
        return self.__y

    def encode_output(self, compressed=True):
        x_bin = self.__x.to_bytes(32, "big")
        if compressed:
            return bytes([2 + (self.__x % 2)]) + x_bin
        y_bin = self.__y.to_bytes(32, "big")
        return b"\x04" + x_bin + y_bin

    @classmethod
    def from_x(cls, x, parity_hint=0):
        return cls(x, point_y(x, parity_hint))

    @classmethod
    def from_hex(cls, pubkey_hex):
        return ECPoint.from_bytes(bytes.fromhex(pubkey_hex))

    @classmethod
    def from_bytes(cls, bytes_data):
        if bytes_data[0] == 4:
            compressed = False
            if len(bytes_data) != 65:
                raise ValueError("Public key uncompressed must be 65 bytes long")
        elif bytes_data[0] == 2 or bytes_data[0] == 3:
            compressed = True
            if len(bytes_data) != 33:
                raise ValueError("Public key compressed must be 33 bytes long")
        else:
            raise ValueError("Invalid X962 public key header")
        px = int.from_bytes(bytes_data[1:33], "big")
        if compressed:
            py = point_y(px, bytes_data[0] - 1)
        else:
            py = int.from_bytes(bytes_data[33:66], "big")
        # check y2 = x3+ax+b
        if pow(py, 2, _p) != (pow(px, 3, _p) + _b) % _p:
            raise ValueError("Public key coordinates are not on the 256k1 curve")
        return cls(px, py)


INFINITY = ECPoint(None, None)
generator_256 = ECPoint(_Gx, _Gy)
neg_generator_256 = ECPoint(_Gx, -_Gy)
p_p1_half = (_p + 1) >> 2


def inverse_mod(a, n):
    """Modular inverse (with a modular prime)"""
    # n prime => ^-1 <> ^( n-2 )
    return pow(a, n - 2, n)


def point_y(px, parity_hint=0):
    """Compute y coordinate from x on the 256k1 curve"""
    xcube = pow(px, 3, _p)
    # p prime => sqrt <> ^( p+1 /2 )
    # y = sqrt(x^3 + 7)
    y = pow(xcube + _b, p_p1_half, _p)
    return y if (y % 2) ^ (parity_hint % 2) else _p - y
