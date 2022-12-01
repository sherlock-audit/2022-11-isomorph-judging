rvierdiiev

medium

# Vault_Velo do not check if liquidator supports ERC721 and sends collateral nft to him unsafely

## Summary
Vault_Velo does not check if liquidator supports ERC721 and sends collateral nft to him unsafely. In case if liquidator can't handle ERC721 then tokens can be stucked inside contract.
## Vulnerability Detail
Vault_Velo._liquidate function sends borrowers Deposited tokens to the liquidator. Later liquidator can make some actions on those tokens to withdraw funds.
Sending logic is done in _returnAndSplitNFTs function.
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Velo.sol#L621-L646
```solidity
    function _returnAndSplitNFTs(
        address _collateralAddress, 
        address _loanHolder, 
        CollateralNFTs calldata _loanNFTs, 
        uint256 _partialPercentage
        ) internal{


        IDepositReceipt depositReceipt = IDepositReceipt(_collateralAddress);
        NFTids storage userNFTs = loanNFTids[_collateralAddress][_loanHolder];
        for(uint256 i = 0; i < NFT_LIMIT; i++){
             //then we check this slot is being used, if not the slot number should be set to `NOT_OWNED`
            if (_loanNFTs.slots[i] < NFT_LIMIT){
                //final slot is NFT that will be split if necessary, we skip this loop if partialPercentage = 100% or 0%
                if((i == NFT_LIMIT -1) && (_partialPercentage > 0) && (_partialPercentage < LOAN_SCALE) ){
                    //split the NFT based on the partialPercentage proposed
                    uint256 newId = depositReceipt.split(_loanNFTs.ids[i], _partialPercentage);
                    //send the new NFT to the user, no mapping to update as original id NFT remains with the vault.
                    depositReceipt.transferFrom(address(this), msg.sender, newId);
                    }
                else{
                    userNFTs.ids[_loanNFTs.slots[i]] = 0;
                    depositReceipt.transferFrom(address(this), msg.sender, _loanNFTs.ids[i]);
                } 
            }
        }
    }
```
Note, that transferFrom function is used instead of safeTransferFrom. That means that in case if liquidator is contract and he doesn't support ERC721, the tokens will stuck there.
## Impact
Liquidated tokens can be stucked.
## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Velo.sol#L647-L700
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Vault_Velo.sol#L621-L646
## Tool used

Manual Review

## Recommendation
Use safeTransferFrom when sending tokens.