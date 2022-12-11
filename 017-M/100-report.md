yixxas

medium

# Multiplication of 3 numbers with 18 decimals can risk overflowing in `callLiquidation()`.

## Summary
Multiplying 3 numbers with `18 decimals` each has a risk of overflowing. Note that `uin256.max` can only hold up to `78 decimals`.

## Vulnerability Detail
In `callLiquidation()`, in both #Vault_Lyra and #Vault_Synths, we compute `isoUSDreturning` with
> `uint256 isoUSDreturning = liquidationAmount*currentPrice*LIQUIDATION_RETURN/LOAN_SCALE/LOAN_SCALE`

We know `LIQUIDATION_RETURN = 95e16` 
This leaves us with about `78 - 18*3 = 22 decimals` remaining for both `liquidationAmount` and `currentPrice`. This means that if the multiplication of `liquidationAmount` and `currentPrice` exceeds `22 decimals` ( about 1 billion for both values if equal ), the liquidation cannot happen.

## Impact
Overflow in `callLiquidation()` can cause the function to revert and prevent values of such liquidation to happen. Malicious users can take a large amount of loan, if price and `liquidationAmount` is high enough, can prevent itself from being liquidated. 

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Lyra.sol#L306
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Synths.sol#L298

## Tool used

Manual Review

## Recommendation
We can change the computation to
`uint256 isoUSDreturning = (liquidationAmount*LIQUIDATION_RETURN/LOAN_SCALE)*currentPrice/LOAN_SCALE`.
This will reduce the risk to a negligible amount due to the unrealistic values required for overflow to happen.
