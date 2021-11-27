from wallets.BTCwallet import testaddr as BTCtestaddr
from wallets.ETHwallet import testaddr as ETHtestaddr
from wallets.LTCwallet import testaddr as LTCtestaddr
from wallets.DOGEwallet import testaddr as DOGEtestaddr
from wallets.EOSwallet import testaddr as EOStestaddr
from wallets.XTZwallet import testaddr as XTZtestaddr


# Tests for addresses formatting

BTC_ADDR_TEST_DATA = [
    #  Address        , isTestnet, Expected check result
    # Good address
    ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", False, True],
    ["1AodSgdggUbwAQryriKcvFYmB3xB53DQpN", False, True],
    ["3MNmH7Bb3oaB9DB8cRf4zBMhD2WiA2pdwb", False, True],
    ["bc1qy6u7ddfx663c8vg6fgfkt9ut2ftmmp5dtyl0kj", False, True],
    # invalid checksum
    ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN1", False, False],
    # a char changed, invalid checksum
    ["1BvBMSEYstWEtqTFn5Au4m4GFg7xJaNVN2", False, False],
    # header changed for testnet
    ["nBvBMSEYstWEtqTFn5Au4m4GFg7xJaNVN2", False, False],
    # header changed
    ["eBvBMSEYstWEtqTFn5Au4m4GFg7xJaNVN2", False, False],
    # Correct address but for testnet
    ["n33YzZo9UNwxbJe5r5qSHePdfXqZLNPChx", False, False],
    # Correct address but for mainnet
    ["1BvBMSEYstWetqTFn5Au4m4GFg7xJaNVN2", True, False],
    ["1AodSgdggUbwAQryriKcvFYmB3xB53DQpN", True, False],
    ["3MNmH7Bb3oaB9DB8cRf4zBMhD2WiA2pdwb", True, False],
    ["bc1qy6u7ddfx663c8vg6fgfkt9ut2ftmmp5dtyl0kj", True, False],
    # Correct testnet address
    ["n33YzZo9UNwxbJe5r5qSHePdfXqZLNPChx", True, True],
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp3", True, True],
    ["2NFq3Wgz1KWhHyLrUnm5aT4k1SmRxZXqhgL", True, True],
    ["tb1qnmnlyacfg5qew8u3zpvs4arzs6qyccy7tanxqm", True, True],
    # invalid checksum
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp2", True, False],
    # a char changed, invalid checksum
    ["mmtSFCh5Sx3V1QHv4cNH4LGH3zMa2oNJp3", True, False],
    # header changed for mainnet
    ["133YzZo9UNwxbJe5r5qSHePdfXqZLNPChx", True, False],
    # header changed
    ["e33YzZo9UNwxbJe5r5qSHePdfXqZLNPChx", True, False],
    # Correct address but for mainnet
    ["1AodSgdggUbwAQryriKcvFYmB3xB53DQpN", True, False],
    # Correct address but for testnet
    ["n33YzZo9UNwxbJe5r5qSHePdfXqZLNPChx", False, False],
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp3", False, False],
    ["2NFq3Wgz1KWhHyLrUnm5aT4k1SmRxZXqhgL", False, False],
    ["tb1qnmnlyacfg5qew8u3zpvs4arzs6qyccy7tanxqm", False, False],
    # valid bech32
    ["BC1QW508D6QEJXTDG4Y5R3ZARVARY0C5XW7KV8F3T4", False, True],
    ["bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", False, True],
    ["tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sl5k7", True, True],
    ["tb1qqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesrxh6hy", True, True],
    ["BC1SW50QGDZ25J", False, True],
    ["bc1zw508d6qejxtdg4y5r3zarvaryvaxxpcs", False, True],
    ["tb1pqqqqp399et2xygdj5xreqhjjvcmzhxw4aywxecjdzew6hylgvsesf3hn0c", True, True],
    ["bc1p2wsldez5mud2yam29q22wgfh9439spgduvct83k3pm50fcxa5dps59h4z5", False, True],
    ["bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqzk5jj0", False, True],
    ["bc1pz37fc4cn9ah8anwm4xqqhvxygjf9rjf2resrw8h8w4tmvcs0863sa2e586", False, True],
    ["bc1pwyjywgrd0ffr3tx8laflh6228dj98xkjj8rum0zfpd6h0e930h6saqxrrm", False, True],
    # Invalid bech32
    ["BC1QW508D6QEJXTDG4Y5r3ZARVARY0C5XW7KV8F3T4", False, False],
    ["bc1qw508d6qejxtdg4y5R3zarvary0c5xw7kv8f3t4", False, False],
    ["tc1qw508d6qejxtdg4y5r3zarvary0c5xw7kg3g4ty", True, False],
    ["bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t5", False, False],
    ["BC13W508D6QEJXTDG4Y5R3ZARVARY0C5XW7KN40WF2", False, False],
    ["bc1rw5uspcuh", False, False],
    ["bc10w508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kw5rljs90", False, False],
    ["BC1QR508D6QEJXTDG4Y5R3ZARVARYV98GJ9P", False, False],
    ["tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3q0sL5k7", True, False],
    ["bc1zw508d6qejxtdg4y5r3zarvaryvqyzf3du", False, False],
    ["tb1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3pjxtptv", True, False],
    ["tc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq5zuyut", True, False],
    ["bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqh2y7hd", False, False],
    ["tb1z0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vqglt7rf", True, False],
    ["BC1S0XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ54WELL", False, False],
    ["bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kemeawh", False, False],
    ["tb1q0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq24jc47", True, False],
    ["bc1p38j9r5y49hruaue7wxjce0updqjuyyx0kh56v8s25huc6995vvpql3jow4", False, False],
    ["BC130XLXVLHEMJA6C4DQV22UAPCTQUPFHLXM9H8Z3K2E72Q4K9HCZ7VQ7ZWS8R", False, False],
    ["bc1pw5dgrnzv", False, False],
    ["bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v8n0nx0muaewav253zgeav", False, False],
    ["tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vq47Zagq", True, False],
    ["bc1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7v07qwwzcrf", False, False],
    ["tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vpggkg4j", True, False],
    ["tb1p1xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vpggkg4j", True, False],
    ["tb1p0xlxvlhemja6c4dqv22uapctqupfhlxm9h8z3k2e72q4k9hcz7vpggkg4e", True, False],
    ["bc1pwyjywgrd0ffr3tx8laflh6228dj98xkjj8rum0zfpd6h0e930h6saqxrsm", False, False],
    ["bc1pwyjywhrd0ffr3tx8laflh6228dj98xkjj8rum0zfpd6h0e930h6saqxrrm", False, False],
    ["bc1pw508d6qejxtdg4y5r3zarvary0c5xw7kw508d6qejxtdg4y5r3zarvary0c5xw7kt5nd6y", False, False],
    ["bc1gmk9yu", False, False],
]

ETH_ADDR_TEST_DATA = [
    #  Address                  ,  Expected check result
    # - Good addresses
    # All caps
    ["0x52908400098527886E0F7030069857D2E4169EE7", True],
    ["0x8617E340B3D01FA5F11F306F4090FD50E238070D", True],
    ["0x82C025c453C9aD2824A9b3710763D90D8F454760", True],
    ["0xfb6916095ca1df60bb79ce92ce3ea74c37c5d359", True],
    # All Lower
    ["0xde709f2102306220921060314715629080e2fb77", True],
    ["0x27b1fdb04752bbc536007a920d24acb045561c26", True],
    ["0xaca128edbd274f2aba534d67dd55ebf67767b9a5", True],
    ["0x82c025c453c9ad2824a9b3710763d90d8f454760", True],
    # Normal EIP55
    ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", True],
    ["0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d359", True],
    ["0xdbF03B407c01E7cD3CBea99509d93f8DDDC8C6FB", True],
    ["0xD1220A0cf47c7B9Be7A2E6BA89F429762e7b9aDb", True],
    ["0xAc1ec44E4f0ca7D172B7803f6836De87Fb72b309", True],
    ["0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed", True],
    ["0xAcA128edBD274F2aBa534d67DD55Ebf67767B9A5", True],
    # - Bad addresses
    # Too short
    ["0xaaeb60f3e94c9b9a09f33669435e7ef1beaed", False],
    ["0xaaeb60f3e94c9b9a09f33669435e7ef1beaed23", False],
    ["0x82c025c453c9ad2824a9b3710763d90d8f4547", False],
    # Bad checksum EIP55
    ["0xfB6916095ca1df60bB79Ce92cE2Ea74c37c5d359", False],
    ["0xfB6916095ca1df60bB79Ce92cE3Ea74c37c5d350", False],
    ["0xfB6916095ca1df60bB79Ce92cE2Ea74c37c5D359", False],
    ["0xFB6916095ca1df60bB79Ce92cE2Ea74c37c5d359", False],
    ["0xFB6916095ca1df60bB79Ce92ce2Ea74c37c5d359", False],
    ["0x8617E340B3D01FA5f11F306F4090FD50E238070D", False],
    ["0xde709f2102306220921060314715629080E2fb77", False],
    # Too long
    ["0xde709f2102306220921060314715629080e2fb771", False],
    ["0xde709f2102306220921060314715629080e2fb7712", False],
    # Not only hex chars
    ["0x5aaeb6053g3e94c9b9a09f33669435e7ef1beaed", False],
    ["0x5aAeb6053G3E94C9b9A09f33669435E7Ef1BeAed", False],
    ["0xz2c025c453c9ad2824a9b3710763d90d8f454760", False],
    ["0xzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", False],
    ["0xzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz", False],
]

LTC_ADDR_TEST_DATA = [
    #  Address       , isTestnet, Expected check result
    # Good address
    ["LUKAFA8Y99pU4zkCFYfZ7RF9wSRhmo8fMQ", False, True],
    ["LMhp8GcaAXBBry2ZyM7EZnfp3RuftnMhDg", False, True],
    ["MHV6KwXikfpNwdrsvPjJFHUYgnVGQRxXb3", False, True],
    ["ltc1qpc9t5jedleg5lg9w0w3kwqmd62hxzyrzphu5aa", False, True],
    # invalid checksum
    ["LUKAFA8Y99pU4zkCFYfZ7RF9wSRhmo8fMP", False, False],
    ["LMhp8GcaAXBBry2ZyM7EZnfp3RuftnMhDh", False, False],
    ["MHV6KwXikfpNwdrsvPjJFHUYgnVGQRxXb2", False, False],
    ["ltc1qpc9t5jedleg5lg9w0w3kwqmd62hxzyrzphu5ab", False, False],
    # a char changed, invalid checksum
    ["LUKAFA9Y99pU4zkCFYfZ7RF9wSRhmo8fMQ", False, False],
    # header changed for testnet
    ["mUKAFA8Y99pU4zkCFYfZ7RF9wSRhmo8fMQ", False, False],
    # header changed
    ["eUKAFA8Y99pU4zkCFYfZ7RF9wSRhmo8fMQ", False, False],
    # Correct address but for testnet
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp3", False, False],
    # Correct address but for mainnet
    ["LUKAFA8Y99pU4zkCFYfZ7RF9wSRhmo8fMQ", True, False],
    ["LMhp8GcaAXBBry2ZyM7EZnfp3RuftnMhDg", True, False],
    ["MHV6KwXikfpNwdrsvPjJFHUYgnVGQRxXb3", True, False],
    ["ltc1qpc9t5jedleg5lg9w0w3kwqmd62hxzyrzphu5aa", True, False],
    # # Correct testnet address
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp3", True, True],
    ["n2c6ZUnBHFkvFdZJU6ERF2P42sFYh89BRj", True, True],
    ["2NFq3Wgz1KWhHyLrUnm5aT4k1SmRxZXqhgL", True, True],
    ["tltc1q03sduszyfq9h3s5m4d4yr8u2tqc95ezpm23ums", True, True],
    # invalid checksum
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp2", True, False],
    # a char changed, invalid checksum
    ["mmtSFCh5Sx3V1QHv4cNH4LGH3zMa2oNJp3", True, False],
    # header changed for mainnet
    ["1mtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp3", True, False],
    # header changed
    ["emtSFCh5Sx3V1QHv4cNH4LGH3zMa2oNJp3", True, False],
    # # Correct address but for mainnet
    ["LUKAFA8Y99pU4zkCFYfZ7RF9wSRhmo8fMQ", True, False],
    # # Correct address but for testnet
    ["mmtSFCh5sx3V1QHv4cNH4LGH3zMa2oNJp3", False, False],
    ["n2c6ZUnBHFkvFdZJU6ERF2P42sFYh89BRj", False, False],
    ["2NFq3Wgz1KWhHyLrUnm5aT4k1SmRxZXqhgL", False, False],
    ["tltc1q03sduszyfq9h3s5m4d4yr8u2tqc95ezpm23ums", False, False],
]

DOGE_ADDR_TEST_DATA = [
    #  Address       , isTestnet, Expected check result
    # Good address
    ["DCU9FQSjMpdZDNPUMNBfHeoodGUjgy36jo", False, True],
    ["DT9gszawp61Qa2NLs7vFaWa1nkRuDbgduy", False, True],
    ["DCiPoYqgDcPSX1Mgv46qyiNTsypypezX1x", False, True],
    ["A2YXMwM3ZgdPzYHsf3GCgscGD6cfcepQda", False, True],
    # invalid checksum
    ["DCU9FQSjMpdZDNPUMNBfHeoodGUjgy36jr", False, False],
    ["DT9gszawp61Qa2NLs8vFaWa1nkRuDbgduy", False, False],
    ["A2YXMwM3ZgdPzYHsf4GCgscGD6cfcepQda", False, False],
    ["DT9gszawp61Qa2NLs7vFaWa1nkRuDbgdvy", False, False],
    ["DT9gszawp61qa2NLs7vFaWa1nkRuDbgduy", False, False],
    # header changed for testnet
    ["mCU9FQSjMpdZDNPUMNBfHeoodGUjgy36jo", False, False],
    ["nCU9FQSjMpdZDNPUMNBfHeoodGUjgy36jo", False, False],
    ["mCiPoYqgDcPSX1Mgv46qyiNTsypypezX1x", False, False],
    ["22YXMwM3ZgdPzYHsf3GCgscGD6cfcepQda", False, False],
    # header changed
    ["eCU9FQSjMpdZDNPUMNBfHeoodGUjgy36jo", False, False],
    # Correct address but for testnet
    ["nmrcMUdt7JNdHBPthpFuvtn9wkKam2SZLH", False, False],
    ["2NA5LtZrNske8yDF2vaqx8QoaPHHAVTpWWG", False, False],
    # Correct address but for mainnet
    ["DCU9FQSjMpdZDNPUMNBfHeoodGUjgy36jo", True, False],
    ["DT9gszawp61Qa2NLs7vFaWa1nkRuDbgduy", True, False],
    ["DCiPoYqgDcPSX1Mgv46qyiNTsypypezX1x", True, False],
    ["A2YXMwM3ZgdPzYHsf3GCgscGD6cfcepQda", True, False],
    # Correct testnet address
    ["nmrcMUdt7JNdHBPthpFuvtn9wkKam2SZLH", True, True],
    ["ndnd3WC9cXutUfTVufJebHfzom1yGd4CNq", True, True],
    ["2NA5LtZrNske8yDF2vaqx8QoaPHHAVTpWWG", True, True],
    # # invalid checksum
    ["nmrcMUdt7JNdHBPthpFuvtn9wkKam2SZLU", True, False],
    ["nmrcMUdt7JNdHBPthpFuvtn8wkKam2SZLH", True, False],
    ["2NA5LTZrNske8yDF2vaqx8QoaPHHAVTpWWG", True, False],
    # header changed for mainnet
    ["1mrcMUdt7JNdHBPthpFuvtn9wkKam2SZLH", True, False],
    # header changed
    ["1mrcMUdt7JNdHBPthpFuvtn9wkKam2SZLH", True, False],
]

# Accounts (destination adresses)
# An account is identified by a human readable of 12 characters in length.
# The characters can include a-z, 1-5, and optional dots (.) except the last character.
EOS_ADDR_TEST_DATA = [
    ["12345abcdefg", True],
    ["hijklmnopqrs", True],
    ["tuvwxyz.1234", True],
    ["111111111111", True],
    ["555555555555", True],
    ["aaaaaaaaaaaa", True],
    ["zzzzzzzzzzzz", True],
    ["eosioaccount", True],
    ["eosio.ccount", True],
    [".osioaccount", True],
    [".osio.ccount", True],
    ["eosioaccoun.", False],
    ["eosioaccOunt", False],
    ["eosioacc?unt", False],
    ["eosXoaccOunt", False],
    ["eos oaccount", False],
    ["", False],
    ["e", False],
    ["eo", False],
    ["eos", False],
    ["eosi", False],
    ["eosio", False],
    ["eosioa", False],
    ["eosioac", False],
    ["eosioacc", False],
    ["eosioacco", False],
    ["eosioaccou", False],
    ["eosioaccoun", False],
    ["eosioaccounta", False],
    ["eosioaccountab", False],
    ["-1", False],
    ["0", False],
    ["6", False],
    ["111111111111k", False],
    ["zzzzzzzzzzzzk", False],
    ["12345abcdefghj", False],
]

XTZ_ADDR_TEST_DATA = [
    # Good addresses
    ["tz1cG2jx3W4bZFeVGBjsTxUAG8tdpTXtE8PT", True],
    ["tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jW", True],
    ["tz1YU2zoyCkXPKEA4jknSpCpMs7yUndVNe3S", True],
    ["tz1XQjK1b3P72kMcHsoPhnAg3dvX1n8Ainty", True],
    ["tz1cipfmtrrpNa3T4rA7bKkFnAa8Zg6GMK7H", True],
    ["tz1ieoXDPfYKyo8HuUqSWWuqWAwrjNvpFcHq", True],
    ["tz1YU2zoyCkXPKEA4jknSpCpMs7yUndVNe3S", True],
    ["tz2FwBnXhuXvPAUcr1aF3uX84Z6JELxrdYxD", True],
    ["tz2JmrN5LtfkYZFCQnWQtwpd9u7Fq3Dc4n6E", True],
    ["tz2HDxspCVakXgHwNfNqngKZxChJsSpJ7wvg", True],
    ["tz3SvEa4tSowHC5iQ8Aw6DVKAAGqBPdyK1MH", True],
    ["tz3Vzw2GYxZQwAfg9ipjNmgAuxgBn3kpDrak", True],
    ["tz3fTJbAxj1LQCEKDKmYLWKP6e5vNC9vwvyo", True],
    ["tz3NXMAoDpaJrtfRhf4NsufScmnJXC4CW5K2", True],
    # Bad addresses
    ["tz1cG2jx3W4bZFeVGBjsTxUAG8tdpTXtE8PU", False],
    ["tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR4jW", False],
    ["tz1YU2zoyCkXPKEA4jknSPCpMs7yUndVNe3S", False],
    ["tz1XQjK1b3P71kMcHsoPhnAg3dvX1n8Ainty", False],
    ["tz1cipfmtrrpNa3T5rA7bKkFnAa8Zg6GMK7H", False],
    ["tz1cG2jx3W4bZFeVGBjsTxUAG8tdpTXtE8P", False],
    ["tz1XVJ8bZUXs7r5NV8dHvuiBhzECvLRLR3jWa", False],
    ["to1YU2zoyCkXPKEA4jknSpCpMs7yUndVNe3S", False],
    ["ez1XQjK1b3P72kMcHsoPhnAg3dvX1n8Ainty", False],
    ["tz2cG2jx3W4bZFeVGBjsTxUAG8tdpTXtE8PT", False],
]


def test_btc_addresses():
    for btc_addr_test in BTC_ADDR_TEST_DATA:
        assert BTCtestaddr(btc_addr_test[0], btc_addr_test[1]) == btc_addr_test[2]


def test_eth_addresses():
    for eth_addr_test in ETH_ADDR_TEST_DATA:
        assert ETHtestaddr(eth_addr_test[0]) == eth_addr_test[1]
        # and also "0x" removed
        assert ETHtestaddr(eth_addr_test[0][2:]) == eth_addr_test[1]


def test_ltc_addresses():
    for ltc_addr_test in LTC_ADDR_TEST_DATA:
        assert LTCtestaddr(ltc_addr_test[0], ltc_addr_test[1]) == ltc_addr_test[2]


def test_doge_addresses():
    for doge_addr_test in DOGE_ADDR_TEST_DATA:
        assert DOGEtestaddr(doge_addr_test[0], doge_addr_test[1]) == doge_addr_test[2]


def test_eos_accounts():
    for eos_addr_test in EOS_ADDR_TEST_DATA:
        assert EOStestaddr(eos_addr_test[0]) == eos_addr_test[1]


def test_xtz_addresses():
    for xtz_addr_test in XTZ_ADDR_TEST_DATA:
        assert XTZtestaddr(xtz_addr_test[0]) == xtz_addr_test[1]
