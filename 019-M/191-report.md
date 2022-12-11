GimelSec

high

# Wrong `CHANGE_COLLATERAL_DELAY` in CollateralBook

## Summary

Admins can bypass time delay due to the wrong value of `CHANGE_COLLATERAL_DELAY`.

## Vulnerability Detail

The comment shows that the `CHANGE_COLLATERAL_DELAY` should be 2 days, but it's only 200 which means 3 minutes and 20 seconds.

## Impact

Admin can bypass the 2 days time delay and only need to wait less than 5 minutes to call `changeCollateralType`.

## Code Snippet

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L23
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L130

## Tool used

Manual Review

## Recommendation

```solidity
uint256 public constant CHANGE_COLLATERAL_DELAY = 2 days; //2 days
```
