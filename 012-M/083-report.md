KingNFT

medium

# The ````viewLiquidatableAmount()```` function will revert unexpectedly when collateral price is low

## Summary
The calculation of ````denominator```` in  ````viewLiquidatableAmount()```` function is with precision loss, the result may be 0 when collateral price is low, cause the function revert unexpectedly.

## Vulnerability Detail
vulnerability point
```solidity
function viewLiquidatableAmount( 
    // ...
    ) public pure returns(uint256){
    // ...
    uint256 numerator =  minimumCollateralPoint - actualCollateralPoint; 
    uint256 denominator = (_collateralPrice*LIQUIDATION_RETURN*_liquidatableMargin/LOAN_SCALE
        - _collateralPrice*LOAN_SCALE)/LOAN_SCALE;
    return(numerator  / denominator); // @audit revert when denominator is 0
}
```

An example
```solidity
LOAN_SCALE = 1e18
LIQUIDATION_RETURN = 0.95e18
_liquidatableMargin = 1.053e18
_collateralPrice = 1000
```
then
```solidity
denominator = (_collateralPrice*LIQUIDATION_RETURN*_liquidatableMargin/LOAN_SCALE
                            - _collateralPrice*LOAN_SCALE)/LOAN_SCALE
            = (1000 * 0.95e18 * 1.053e18 / 1e18 - 1000 * 1e18 ) / 1e18
            = (1000.35e18 - 1000e28) / 1e18
            = 0.35e18 / 1e18
            = 0
```

## Impact
````viewLiquidatableAmount```` is called by ````callLiquidation````, so while collateral price is low enough, liquidation will fail.

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Base_ERC20.sol#L408

## Tool used

Manual Review

## Recommendation
```diff
function viewLiquidatableAmount(
    uint256 _collateralAmount,
    uint256 _collateralPrice,
    uint256 _userDebt,
    uint256 _liquidatableMargin
    ) public pure returns(uint256){
    uint256 minimumCollateralPoint = _userDebt*_liquidatableMargin;
    uint256 actualCollateralPoint = _collateralAmount*_collateralPrice;
    if(minimumCollateralPoint <=  actualCollateralPoint){
        //in this case the loan is not liquidatable at all and so we return zero
        return 0;
    }
    uint256 numerator =  minimumCollateralPoint - actualCollateralPoint; 
    uint256 denominator = (_collateralPrice*LIQUIDATION_RETURN*_liquidatableMargin/LOAN_SCALE - _collateralPrice*LOAN_SCALE)/LOAN_SCALE;
+   if (denominator == 0) return _collateralAmount;
    return(numerator  / denominator);

}
```
