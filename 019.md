rvierdiiev

medium

# CollateralBook queueCollateralChange, changeCollateralType and addCollateralType functions doesn't check that _interestPer3Min is bigger than DIVISION_BASE

## Summary
CollateralBook queueCollateralChange, changeCollateralType and addCollateralType functions doesn't check that _interestPer3Min is bigger than DIVISION_BASE. If smaller than DIVISION_BASE value will be provided than function _updateVirtualPriceAndTime will always revert.
## Vulnerability Detail
Owner can provide _interestPer3Min param for a collateral using 3 functions: queueCollateralChange, changeCollateralType and addCollateralType.
Any of this function checks that _interestPer3Min is bigger than DIVISION_BASE.
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L258-L271
```solidity
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

If less value than DIVISION_BASE is provided that means that collateral.virtualPrice will start decreasing. And the check in _updateVirtualPriceAndTime function will not pass.
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L231-L241
```solidity
    function _updateVirtualPriceAndTime(
        address _collateralAddress,
        uint256 _virtualPriceUpdate,
        uint256 _updateTime
        ) internal  {


        require( collateralProps[_collateralAddress].virtualPrice < _virtualPriceUpdate, "Incorrect virtual price" );
        require( collateralProps[_collateralAddress].lastUpdateTime < _updateTime, "Incorrect timestamp" );
        collateralProps[_collateralAddress].virtualPrice = _virtualPriceUpdate;
        collateralProps[_collateralAddress].lastUpdateTime = _updateTime;
    }
```

As result it will be not possible to update virtual price and all functions that depends on _updateVirtualPriceAndTime will revert.
## Impact
It will be not possible to update virtual price using updateVirtualPriceSlowly function.
## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L117
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L152
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L313
## Tool used

Manual Review

## Recommendation
Check that _interestPer3Min is bigger than DIVISION_BASE.