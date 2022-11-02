from io import BytesIO
import urllib.request
from json import load

from cryptolib.coins.ethereum import read_int_array, read_string, uint256


IPFS_GATEWAY = "https://cloudflare-ipfs.com/ipfs/"

# walletOfOwner(address)
WALLETOWNER_FUNCTION = "438b6300"
# tokenURI(uint256)
TOKENURI_FUNCTION = "c87b56dd"


def get_data(url):
    url = url.replace("ipfs://", IPFS_GATEWAY)
    rfile = urllib.request.urlopen(url)
    return rfile


def get_image_file(url):
    return BytesIO(get_data(url).read())


class NFTWallet:
    def __init__(self, wallet):
        self.wallet = wallet

    def get_balance(self):
        """balanceOf"""
        return self.wallet.eth.getbalance(False)

    def get_symbol(self):
        return self.wallet.coin

    def get_tokens_list(self, balance):

        arr_idxs = []

        try:
            idsraw = self.wallet.eth.call(
                WALLETOWNER_FUNCTION, f"000000000000000000000000{self.wallet.eth.address}"
            )
            # table of indexes
            arr_idxs = read_int_array(idsraw)
        except Exception:
            pass

        # tokenOfOwnerByIndex(address _owner, uint256 _index)
        # tokenOfOwnerByIndex(address,uint256)
        # tokID = "2f745c59"
        # balraw = wallet.eth.api.call(contract, tokID)
        # print(int(balraw[2:], 16))

        if len(arr_idxs) != balance:
            raise Exception("Unmatched NFT data.")
        return arr_idxs

    def get_metadata(self, id):
        # tokenURI( TokenID )
        balraw = self.wallet.eth.call(TOKENURI_FUNCTION, uint256(id).hex())
        metadata_url = read_string(balraw)
        metadata = {}
        if metadata_url is not None:
            metadata_stream = get_data(metadata_url)
            metadata = load(metadata_stream)
        return metadata
