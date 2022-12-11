0x52

medium

# Vault_Base_ERC20#_updateVirtualPrice calculates interest incorrectly if updated frequently

## Summary

Updating the virtual price of an asset happens in discrete increments of 3 minutes. This is done to reduce the chance of DOS loops. The issue is that it updates the time to an incorrect timestamp. It should update to the truncated 3 minute interval but instead updates to the current timestamp. The result is that the interest calculation can be abused to lower effective interest rate.

## Vulnerability Detail

    function _updateVirtualPrice(uint256 _currentBlockTime, address _collateralAddress) internal { 
        (   ,
            ,
            ,
            uint256 interestPer3Min,
            uint256 lastUpdateTime,
            uint256 virtualPrice,

        ) = _getCollateral(_collateralAddress);
        uint256 timeDelta = _currentBlockTime - lastUpdateTime;
        //exit gracefully if two users call the function for the same collateral in the same 3min period
        //@audit increments 
        uint256 threeMinuteDelta = timeDelta / 180; 
        if(threeMinuteDelta > 0) {
            for (uint256 i = 0; i < threeMinuteDelta; i++ ){
            virtualPrice = (virtualPrice * interestPer3Min) / LOAN_SCALE; 
            }
            collateralBook.vaultUpdateVirtualPriceAndTime(_collateralAddress, virtualPrice, _currentBlockTime);
        }
    }

_updateVirtualPrice is used to update the interest calculations for the specified collateral and is always called with block.timestamp. Due to truncation threeMinuteDelta is always rounded down, that is if there has been 1.99 3-minute intervals it will truncate to 1. The issue is that in the collateralBook#vaultUpdateVirtualPriceAndTime subcall the time is updated to block.timestamp (_currentBlockTime). 

Example:
lastUpdateTime = 1000 and block.timestamp (_currentBlockTime) = 1359.

timeDelta = 1359 - 1000 = 359

threeMinuteDelta = 359 / 180 = 1

This updates the interest by only as single increment but pushes the new time forward 359 seconds. When called again it will use 1359 as lastUpdateTime which means that 179 seconds worth of interest have been permanently lost. Users with large loan positions could abuse this to effectively halve their interest accumulation. Given how cheap optimism transactions are it is highly likely this could be exploited profitably with a bot.

## Impact

Interest calculations will be incorrect if they are updated frequently, which can be abused by users with large amounts of debt to halve their accumulated interest

## Code Snippet

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Base_ERC20.sol#L203-L221

## Tool used

Manual Review

## Recommendation

Before updating the interest time it should first truncate it to the closest 3-minute interval:

        if(threeMinuteDelta > 0) {
            for (uint256 i = 0; i < threeMinuteDelta; i++ ){
                virtualPrice = (virtualPrice * interestPer3Min) / LOAN_SCALE; 
            }
    +       _currentBlockTime = (_currentBlockTime / 180) * 180;
            collateralBook.vaultUpdateVirtualPriceAndTime(_collateralAddress, virtualPrice, _currentBlockTime);
        }