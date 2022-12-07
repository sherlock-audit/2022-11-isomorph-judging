Jeiwan

medium

# Dangerous assumption on the peg of USDC can lead to manipulations

## Summary
Dangerous assumption on the peg of USDC can lead to manipulations
## Vulnerability Detail
When pricing liquidity of a Velodrome USDC pool, it's assumed that hte price of USDC is exactly $1 ([DepositReceipt_USDC.sol#L100](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L100), [DepositReceipt_USDC.sol#L123](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L123)). However, in reality, there's no hard peg, the price can go both above or below $1 (https://coinmarketcap.com/currencies/usd-coin/).

The volatility of USDC will also affect the price of the other token in the pool since it's priced in USDC ([DepositReceipt_USDC.sol#L87](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L87), [DepositReceipt_USDC.sol#L110](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L110)) and then compared to its USD price from a Chainlink oracle ([DepositReceipt_USDC.sol#L90-L98](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L90-L98)).

This issue is also applicable to the hard coded peg of sUSD when evaluating the USD price of a Synthetix collateral ([Vault_Synths.sol#L76](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Synths.sol#L76)):
```solidity
/// @return returns the value of the given synth in sUSD which is assumed to be pegged at $1.
function priceCollateralToUSD(bytes32 _currencyKey, uint256 _amount) public view override returns(uint256){
    //As it is a synth use synthetix for pricing
    return (synthetixExchangeRates.effectiveValue(_currencyKey, _amount, SUSD_CODE));      
}
```
And sUSD is even less stable than USDC (https://coinmarketcap.com/currencies/susd/).

Together with isoUSD not having a stability mechanism, these assumptions can lead to different manipulations with the price of isoUSD and the arbitraging opportunities created by the hard peg assumptions (sUSD and USDC will be priced differently on exchanges and on Isomorph).

## Impact
If the price of USDC falls below $1, collateral will be priced higher than expected. This will keep borrowers from being liquidated. And it will probably affect the price of isoUSD since there will be an arbitrage opportunity: the cheaper USDC will be priced higher as collateral on Isomorph.
If hte price of USDC raises above $1, borrowers' collateral will be undervalued and some liquidations will be possible that wouldn't have be allowed if the actual price of USDC was used.

## Code Snippet
The value of USDC equals its amount ([DepositReceipt_USDC.sol#L100](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L100), [DepositReceipt_USDC.sol#L123](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L123)):
```solidity
value0 = token0Amount * SCALE_SHIFT;
```

The other token in a pool is priced in USDC ([DepositReceipt_USDC.sol#L87](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L87), [DepositReceipt_USDC.sol#L110](https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/DepositReceipt_USDC.sol#L110)):
```solidity
(amountOut, stablePool) = router.getAmountOut(HUNDRED_TOKENS, token1, USDC);
```
## Tool used
Manual Review

## Recommendation
Consider using the Chainlink USDC/USD feed to get the price of USDC and price liquidity using the actual price of USDC. Also, consider converting sUSD prices of Synthetix collaterals to USD to mitigate the discrepancy in prices between external exchanges and Isomorph.