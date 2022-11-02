from io import BytesIO
from logging import getLogger
import urllib.request
from json import load

from cryptolib.coins.ethereum import read_int_array, read_string, uint256


IPFS_GATEWAY = "https://cloudflare-ipfs.com/ipfs/"

# walletOfOwner(address)
WALLETOWNER_FUNCTION = "438b6300"
# tokenURI(uint256)
TOKENURI_FUNCTION = "c87b56dd"
# tokenOfOwnerByIndex(address,uint256)
TOKENSOWNER_FUNCTION = "2f745c59"


logger = getLogger(__name__)


def get_data(url, retry=0):
    if retry == 0:
        url = url.replace("ipfs://", IPFS_GATEWAY)
    logger.debug("Reading %s", url)
    try:
        rfile = urllib.request.urlopen(url)
        return rfile
    except Exception as exc:
        # Retry
        if retry <= 4:
            logger.error("Error %s", str(exc))
            retry += 1
            logger.debug("Retry #%i", retry)
            return get_data(url, retry)
        raise exc


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
                WALLETOWNER_FUNCTION,
                f"000000000000000000000000{self.wallet.eth.address}"
            )
            # table of indexes
            arr_idxs = read_int_array(idsraw)
        except Exception:
            pass

        if balance > 0 and len(arr_idxs) == 0:
            for oidx in range(balance):
                idxraw = self.wallet.eth.call(
                    TOKENSOWNER_FUNCTION,
                    f"000000000000000000000000{self.wallet.eth.address}"
                    f"{uint256(oidx).hex()}"
                )
                idx = int(idxraw[2:], 16)
                logger.debug("NFT #%i has id = %i", oidx, idx)
                arr_idxs.append(idx)

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
