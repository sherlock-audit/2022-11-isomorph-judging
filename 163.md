zimu

medium

# `Depositor` does not consider fee-on-transfer/deflationary AMM tokens

## Summary
`Depositor` does not consider fee-on-transfer/deflationary AMM tokens. In this case, users will be unable to call `depositToGauge()` and `withdrawFromGauge()` due to not enough assets in the contract.

## Vulnerability Detail
Assume that `AMMToken` has `1%` fee when transfer. In `Depositor`, function `depositToGauge()` will be unable to execute `gauge.deposit(_amount, 0)` since the contract only holds `99% _amount` of `AMMToken` after performing `AMMToken.transferFrom(msg.sender, address(this), _amount)`. And similarly, function `withdrawFromGauge` also cannot execute ` AMMToken.transfer(msg.sender, amount)` without enough `AMMToken`.
```solidity
    function depositToGauge(uint256 _amount) onlyOwner() external returns(uint256){
        AMMToken.transferFrom(msg.sender, address(this), _amount);
        AMMToken.safeIncreaseAllowance(address(gauge), _amount);
        gauge.deposit(_amount, 0);
        uint256 NFTId = depositReceipt.safeMint(_amount);
        depositReceipt.safeTransferFrom(address(this), msg.sender, NFTId);
        return(NFTId);
    }

    function withdrawFromGauge(uint256 _NFTId, address[] memory _tokens)  public  {
        uint256 amount = depositReceipt.pooledTokens(_NFTId);
        depositReceipt.burn(_NFTId);
        gauge.getReward(address(this), _tokens);
        gauge.withdraw(amount);
        AMMToken.transfer(msg.sender, amount);
    }
```

## Impact
The protocol will be unable to pay enough tokens when users want to call `depositToGauge()` and `withdrawFromGauge()`.

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/Depositor.sol#L58-L70
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Velo-Deposit-Tokens/contracts/Depositor.sol#L119-L127

## Tool used
Manual Review

## Recommendation
Check balance after transfer:
```solidity
  function depositToGauge(uint256 _amount) onlyOwner() external returns(uint256){
      AMMToken.transferFrom(msg.sender, address(this), _amount);
+     _amount = AMMToken.balanceOf(address(this));
      AMMToken.safeIncreaseAllowance(address(gauge), _amount);
      gauge.deposit(_amount, 0);
      uint256 NFTId = depositReceipt.safeMint(_amount);
      depositReceipt.safeTransferFrom(address(this), msg.sender, NFTId);
      return(NFTId);
  }

  function withdrawFromGauge(uint256 _NFTId, address[] memory _tokens)  public  {
      uint256 amount = depositReceipt.pooledTokens(_NFTId);
      depositReceipt.burn(_NFTId);
      gauge.getReward(address(this), _tokens);
      gauge.withdraw(amount);
+     amount = AMMToken.balanceOf(address(this));
      AMMToken.transfer(msg.sender, amount);
  }
```