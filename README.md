# ftm-gas-monetization-contracts

### Mythril - Audit tool
To run [Mythril](https://mythril-classic.readthedocs.io/en/develop/index.html), connect to `brownie` container 
(where all dependencies are installed) and run following command.
```
myth analyze contracts/GasMonetization.sol --solc-json mythril.json
```