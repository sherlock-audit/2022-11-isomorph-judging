GimelSec

high

# `liquidityPoolOf` is easy to overwrite, A malicious admin can use a fake liquidityPool control the price of collateral in `Vault_Lyra`

## Summary

A malicious admin can use a fake liquidityPool to control the token price in `Vault_Lyra.priceCollateralToUSD`. Also he/she can make `Vault_Lyra._checkIfCollateralIsActive` return false.

## Vulnerability Detail

`collateralBook.liquidityPoolOf(_currencyKey)` is used in`Vault_Lyra.priceCollateralToUSD` and `Vault_Lyra._checkIfCollateralIsActive`. The `LiquidityPool` is very important in `Vault_Lyra`  

```solidity
    function priceCollateralToUSD(bytes32 _currencyKey, uint256 _amount) public view override returns(uint256){
         //The LiquidityPool associated with the LP Token is used for pricing
        ILiquidityPoolAvalon LiquidityPool = ILiquidityPoolAvalon(collateralBook.liquidityPoolOf(_currencyKey));
        //we have already checked for stale greeks so here we call the basic price function.
        uint256 tokenPrice = LiquidityPool.getTokenPrice();          
        uint256 withdrawalFee = _getWithdrawalFee(LiquidityPool);
        uint256 USDValue  = (_amount * tokenPrice) / LOAN_SCALE;
        //we remove the Liquidity Pool withdrawalFee 
        //as there's no way to remove the LP position without paying this.
        uint256 USDValueAfterFee = USDValue * (LOAN_SCALE- withdrawalFee)/LOAN_SCALE;
        return(USDValueAfterFee);
    }

    function _checkIfCollateralIsActive(bytes32 _currencyKey) internal view override {
            
             //Lyra LP tokens use their associated LiquidityPool to check if they're active
             ILiquidityPoolAvalon LiquidityPool = ILiquidityPoolAvalon(collateralBook.liquidityPoolOf(_currencyKey));
             bool isStale;
             uint circuitBreakerExpiry;
             //ignore first output as this is the token price and not needed yet.
             (, isStale, circuitBreakerExpiry) = LiquidityPool.getTokenPriceWithCheck();
             require( !(isStale), "Global Cache Stale, can't trade");
             require(circuitBreakerExpiry < block.timestamp, "Lyra Circuit Breakers active, can't trade");
    }
```

However, `liquidityPoolOf` is easy to overwrite by simply calling `CollateralBook.addCollateralType`. A malicious admin can use a fake `LiquidityPool` to control the price of collateral in `Vault_Lyra`.

```solidity
    function addCollateralType(
        address _collateralAddress,
        bytes32 _currencyKey,
        uint256 _minimumRatio,
        uint256 _liquidationRatio,
        uint256 _interestPer3Min,
        uint256 _assetType,
        address _liquidityPool
        ) external onlyAdmin {

        require(!collateralValid[_collateralAddress], "Collateral already exists");
        require(!collateralPaused[_collateralAddress], "Collateral already exists");
        require(_collateralAddress != address(0));
        require(_minimumRatio > _liquidationRatio);
        require(_liquidationRatio > 0);
        require(vaults[_assetType] != address(0), "Vault not deployed yet");
        IVault vault = IVault(vaults[_assetType]);

        //prevent setting liquidationRatio too low such that it would cause an overflow in callLiquidation, see appendix on liquidation maths for details.
        require( vault.LIQUIDATION_RETURN() *_liquidationRatio >= 10 ** 36, "Liquidation ratio too low"); //i.e. 1 when multiplying two 1 ether scale numbers.
        collateralValid[_collateralAddress] = true;
        collateralProps[_collateralAddress] = Collateral(
            _currencyKey,
            _minimumRatio,
            _liquidationRatio,
            _interestPer3Min,
            block.timestamp,
            1 ether,
            _assetType
            );
        //Then update LiqPool as this isn't stored in the struct and requires the currencyKey also.
        liquidityPoolOf[_currencyKey]= _liquidityPool; 
    }
```


## Impact
A malicious admin can use the fake `LiquidityPool` to control the price of the collateral. Also, he/she can block `openLoan`, `increaseCollateralAmount`, `closeLoan` and `callLiquidation` by making `Vault_Lyra._checkIfCollateralIsActive` return false.

## Code Snippet

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L319

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Lyra.sol#L48

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Lyra.sol#L79


## Tool used

Manual Review

## Recommendation

Add a check in `addCollateralType`. Make sure that the admin cannot overwrite existed `liquidityPool`.

```solidity
    function addCollateralType(
        address _collateralAddress,
        bytes32 _currencyKey,
        uint256 _minimumRatio,
        uint256 _liquidationRatio,
        uint256 _interestPer3Min,
        uint256 _assetType,
        address _liquidityPool
        ) external onlyAdmin {

        require(!collateralValid[_collateralAddress], "Collateral already exists");
        require(!collateralPaused[_collateralAddress], "Collateral already exists");
        require(_collateralAddress != address(0));
        require(_minimumRatio > _liquidationRatio);
        require(_liquidationRatio > 0);
+       require(liquidityPoolOf[_currencyKey] == address(0));
        require(vaults[_assetType] != address(0), "Vault not deployed yet");
        IVault vault = IVault(vaults[_assetType]);

        //prevent setting liquidationRatio too low such that it would cause an overflow in callLiquidation, see appendix on liquidation maths for details.
        require( vault.LIQUIDATION_RETURN() *_liquidationRatio >= 10 ** 36, "Liquidation ratio too low"); //i.e. 1 when multiplying two 1 ether scale numbers.
        collateralValid[_collateralAddress] = true;
        collateralProps[_collateralAddress] = Collateral(
            _currencyKey,
            _minimumRatio,
            _liquidationRatio,
            _interestPer3Min,
            block.timestamp,
            1 ether,
            _assetType
            );
        //Then update LiqPool as this isn't stored in the struct and requires the currencyKey also.
        liquidityPoolOf[_currencyKey]= _liquidityPool; 
    }
```
