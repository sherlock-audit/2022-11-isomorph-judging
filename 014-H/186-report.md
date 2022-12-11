GimelSec

high

# The admin of `CollateralBook` can use a malicious `vault` to bypass the `liquidationRatio` check in `CollateralBook.queueCollateralChange`

## Summary

To prevent setting liquidationRatio too low, it would check `vault.LIQUIDATION_RETURN() *_liquidationRatio >= 10 ** 36` in `CollateralBook.queueCollateralChange()`. But the admin can use a malicious `vault` to bypass the check.

## Vulnerability Detail

In `CollateralBook.queueCollateralChange()` it would check whether ` vault.LIQUIDATION_RETURN() *_liquidationRatio >= 10 ** 36`. The `vault` is `vaults[_assetType]`. Which means the admin can use any vault to do the check. And there is no check for `_assetType`.

```solidity
    function queueCollateralChange(
        address _collateralAddress,
        bytes32 _currencyKey,
        uint256 _minimumRatio,
        uint256 _liquidationRatio,
        uint256 _interestPer3Min,
        uint256 _assetType,
        address _liquidityPool

    ) external collateralExists(_collateralAddress) onlyAdmin {
        require(_collateralAddress != address(0));
        require(_minimumRatio > _liquidationRatio);
        require(_liquidationRatio != 0);
        require(vaults[_assetType] != address(0), "Vault not deployed yet");
        IVault vault = IVault(vaults[_assetType]);
        //prevent setting liquidationRatio too low such that it would cause an overflow in callLiquidation, see appendix on liquidation maths for details.
        require( vault.LIQUIDATION_RETURN() *_liquidationRatio >= 10 ** 36, "Liquidation ratio too low");

        queuedCollateralAddress = _collateralAddress;
        queuedCurrencyKey = _currencyKey;
        queuedMinimumRatio = _minimumRatio;
        queuedLiquidationRatio = _liquidationRatio;
        queuedInterestPer3Min = _interestPer3Min;
        queuedLiquidityPool = _liquidityPool;
        queuedTimestamp = block.timestamp;
    }
```
Also, the admin can easily add a malicious vault by calling `addVaultAddress()`

```solidity
    function addVaultAddress(address _vault, uint256 _assetType) external onlyAdmin{
        require(_vault != address(0), "Zero address");
        require(vaults[_assetType] == address(0), "Asset type already has vault");
        _setupRole(VAULT_ROLE, _vault);
        vaults[_assetType]= _vault;
    }
``` 

In conclusion, a malicious admin can first add a malicious vault. Then use the malicious vault to bypass the `liquidationRatio` check in `CollateralBook.queueCollateralChange()`.


## Impact

If the `liquidationRatio` check is bypassed, The liquidationRatio could be too low such that it would cause an overflow in callLiquidation.

## Code Snippet

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L109

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L111

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/CollateralBook.sol#L216

## Tool used

Manual Review

## Recommendation

`assetType` is stored in `collateralProps`. So `queueCollateralChange` should use that instead of `_assetType` which is provided by the caller.

```solidity
    function queueCollateralChange(
        address _collateralAddress,
        bytes32 _currencyKey,
        uint256 _minimumRatio,
        uint256 _liquidationRatio,
        uint256 _interestPer3Min,
-       uint256 _assetType,
        address _liquidityPool

    ) external collateralExists(_collateralAddress) onlyAdmin {
        require(_collateralAddress != address(0));
        require(_minimumRatio > _liquidationRatio);
        require(_liquidationRatio != 0);
        require(vaults[_assetType] != address(0), "Vault not deployed yet");
-       IVault vault = IVault(vaults[_assetType]);
+       IVault vault = IVault(vaults[collateralProps[_collateralAddress].assetType]);
        //prevent setting liquidationRatio too low such that it would cause an overflow in callLiquidation, see appendix on liquidation maths for details.
        require( vault.LIQUIDATION_RETURN() *_liquidationRatio >= 10 ** 36, "Liquidation ratio too low");

        queuedCollateralAddress = _collateralAddress;
        queuedCurrencyKey = _currencyKey;
        queuedMinimumRatio = _minimumRatio;
        queuedLiquidationRatio = _liquidationRatio;
        queuedInterestPer3Min = _interestPer3Min;
        queuedLiquidityPool = _liquidityPool;
        queuedTimestamp = block.timestamp;
    }
```
