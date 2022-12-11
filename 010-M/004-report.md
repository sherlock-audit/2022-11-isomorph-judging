Haruxe

high

# `_updateVirtualPrice` After Prolonged Inactivity Will Brick Vaults

## Summary
In `Vault_Base_ERC20.sol`, the `_updateVirtualPrice` function is called whenever the latest price is fetched in order to update the most up-to-date price. The `threeMinuteDelta` variable increments every 3 minutes, and is looped over to update the virtual price for each three minutes. But, this execution could run out of gas due to inactivity.

### `Vault_Base_ERC20.sol` LN#212
```solidity
uint256 timeDelta = _currentBlockTime - lastUpdateTime;
//exit gracefully if two users call the function for the same collateral in the same 3min period
uint256 threeMinuteDelta = timeDelta / 180; 
```
## Vulnerability Detail
The problem lies in the `threeMinuteDelta` delta calculation. Looping over the size of this variable could soon turn very sour when if a certain vault implements this contract and functions and goes inactive for an extended period of time - all funds and operations will be lost.

In a lesser extent, even if it does not run out of gas - the end user will burn enormous funds on gas to front the operation costs. Users may even backrun/wait for another user to front the bill.

### `Vault_Base_ERC20.sol` LN#215
```solidity
if(threeMinuteDelta > 0) {
            for (uint256 i = 0; i < threeMinuteDelta; i++ ){
            virtualPrice = (virtualPrice * interestPer3Min) / LOAN_SCALE; 
            }
            collateralBook.vaultUpdateVirtualPriceAndTime(_collateralAddress, virtualPrice, _currentBlockTime);
        }
```

The current solution to this problem comes in the form of `updateVirtualPriceSlowly()`, where anyone can set the virtual price's latest update - but has some problems of its own.

### `CollateralBank.sol` LN#254-271
```solidity
    /// @dev this function is intentionally callable by anyone
    /// @notice it is designed to prevent DOS situations occuring if there is a long period of inactivity for a collateral token
    /// @param _collateralAddress the collateral token you are updating the virtual price of
    /// @param _cycles how many updates (currently equal to seconds) to process the virtual price for.
    function updateVirtualPriceSlowly(
        address _collateralAddress,
        uint256 _cycles
        ) public collateralExists(_collateralAddress){ 
            Collateral memory collateral = collateralProps[_collateralAddress];
            uint256 timeDelta = block.timestamp - collateral.lastUpdateTime;
            uint256 threeMinDelta = timeDelta / THREE_MIN;
    
            require(_cycles <= threeMinDelta, 'Cycle count too high');
                for (uint256 i = 0; i < _cycles; i++ ){
                    collateral.virtualPrice = (collateral.virtualPrice * collateral.interestPer3Min) / DIVISION_BASE; 
                }
            _updateVirtualPriceAndTime(_collateralAddress, collateral.virtualPrice, collateral.lastUpdateTime + (_cycles*THREE_MIN));
        }
```

Lets say a deal of time has passed since a collateral was updated, and the `latestUpdate` has exceeded the limit for the functions in the vaults contracts to resolve themselves leading to the DOS situation. This will require enough `cycles` in the params for the latest update to be in the gas range that the vaults will no longer run out.

The incentives for users to call the `updateVirtualPrice()` is insanely low as they will be much more likely to wait for someone to update the values themselves while the vaults are still inaccessible (including not being able to liquidate qualifying loans), as well as most users will not be notified on the front-end to notify them of this problem - leading to some unhappy users with locked funds.

If this persists, an enormous amount of gas will be used just to calculate the `callateralProps[]` that information of collaterals come from - and/or intervention will be necessary from an admin by calling the role locked `vaultUpdateVirtualPriceAndTime()` function.

### `CollateralBank.sol` LN#243-251
```solidity
    /// @dev external function to enable the Vault to update the collateral virtual price & update timestamp
    ///      while maintaining the same method as the slow update below for consistency.
    function vaultUpdateVirtualPriceAndTime(
        address _collateralAddress,
        uint256 _virtualPriceUpdate,
        uint256 _updateTime
    ) external onlyVault collateralExists(_collateralAddress){
        _updateVirtualPriceAndTime(_collateralAddress, _virtualPriceUpdate, _updateTime);
    }
```

In addition, in `CollateralBook.sol`, the admin(s) will no longer be able to change collateral types without intervention, calling either `vaultUpdateVirtualPriceAndTime()` or `updateVirtualPriceSlowly()` to prevent `updateVirtualPriceSlowly()` in `changeCollateralType()` from running out of gas.

### 

## Impact
Since `Vault_Lyra.sol`, `Vault_Synths.sol`, and `Vault_Velo.sol` all inherit from `Vault_Base_ERC20.sol` and use the `_updateVirtualPrice` for opening, closing, and interacting with loans, once the `threeMinuteDelta` gets to an unreachable number they will no longer be intractable as every transaction will revert before reaching success until intervention occurs.

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Base_ERC20.sol#L199-L221
## Tool used

Manual Review

## Recommendation

Set an upper limit for `threeMinuteDelta`.