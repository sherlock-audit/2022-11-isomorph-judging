hansfriese

medium

# Wrong constants for time delay



## Summary
This protocol uses several constants for time dealy and some of them are incorrect.

## Vulnerability Detail
In `isoUSDToken.sol`, `ISOUSD_TIME_DELAY` should be `3 days` instead of 3 seconds.

```solidity
    uint256 constant ISOUSD_TIME_DELAY = 3; // days;
```

In `CollateralBook.sol`, `CHANGE_COLLATERAL_DELAY` should be `2 days` instead of 200 seconds.

```solidity
    uint256 public constant CHANGE_COLLATERAL_DELAY = 200; //2 days
```

## Impact
Admin settings would be updated within a short period of delay so that users wouldn't react properly.

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/isoUSDToken.sol#L10
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L23

## Tool used
Manual Review

## Recommendation
2 constants should be modified as mentioned above.