KingNFT

high

# The calculation of ````totalUSDborrowed```` in ````openLoan()```` is not correct

## Summary
The ````openLoan()```` function  wrongly use ````isoUSDLoaned```` to calculate ````totalUSDborrowed````. Attacker can exploit it to bypass security check and loan isoUSD with no enough collateral.

## Vulnerability Detail
vulnerability point
```solidity
function openLoan(
    // ...
    ) external override whenNotPaused 
    {
    //...
    uint256 colInUSD = priceCollateralToUSD(currencyKey, _colAmount
                        + collateralPosted[_collateralAddress][msg.sender]);
    uint256 totalUSDborrowed = _USDborrowed 
        +  (isoUSDLoaned[_collateralAddress][msg.sender] * virtualPrice)/LOAN_SCALE;
        // @audit should be isoUSDLoanAndInterest[_collateralAddress][msg.sender]
    require(totalUSDborrowed >= ONE_HUNDRED_DOLLARS, "Loan Requested too small");
    uint256 borrowMargin = (totalUSDborrowed * minOpeningMargin) / LOAN_SCALE;
    require(colInUSD >= borrowMargin, "Minimum margin not met!");

    // ...
}
```
Attack example:
<1>Attacker normally loans and produces 10000 isoUSD interest
<2>Attacker repays principle but left interest
<3>Attacker open a new 10000 isoUSD loan without providing collateral
## Impact
Attacker can loan isoUSD with no enough collateral.

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Synths.sol#L120

## Tool used

Manual Review

## Recommendation
See Vulnerability Detail
