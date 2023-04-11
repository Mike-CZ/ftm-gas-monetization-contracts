# ftm-gas-monetization-contracts

### Deploy
To deploy contract on fantom-opera, run 
```
brownie run --network=ftm-main deploy
```
You might need to add your account by importing private key to interact with blockchain.
```
brownie accounts new <identifier>
```
And then enter your private key.

#### Publishing sources
You need to export ftmscan api key before running deployment. Obtain api key and run
```
export FTMSCAN_TOKEN=<my_ftmscan_token>
```


### Mythril - Audit tool
To run [Mythril](https://mythril-classic.readthedocs.io/en/develop/index.html), connect to `brownie` container 
(where all dependencies are installed) and run following command.
```
myth analyze contracts/GasMonetization.sol --solc-json mythril.json
```