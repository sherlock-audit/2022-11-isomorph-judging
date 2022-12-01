KingNFT

medium

# A removed minter can be added again without new proposal and time delay lock

## Summary
The 'addRole()' function of AccessControl.sol is missing to clear proposal data, causes a removed minter can be added again without new proposal and time delay lock.

## Vulnerability Detail
Steps:
(1) Admin A proposes a minter
```solidity
proposeAddRole(minter, MINTER_ROLE);
```
(2) time delay pass
(3) Admin A makes the minter effective.
```solidity
addRole(minter, MINTER_ROLE);
```
(4) Admin B removes the minter
```solidity
removeRole(minter, MINTER_ROLE);
```
(5) Admin A adds minter again without new proposal and time delay lock
```solidity
addRole(minter, MINTER_ROLE);
```

## Impact
Proposal and time delay lock is bypassed.

## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/RoleControl.sol#L47
```solidity
function proposeAddRole(address _account, bytes32 _role) external onlyAdmin{
    bytes32 action_hash = keccak256(abi.encode(_account, _role, actionNonce));
    previous_action_hash = action_hash;
    actionNonce += 1;
    action_queued[action_hash] = block.timestamp;
    emit QueueAddRole(_account, _role, msg.sender, block.timestamp);
}

function addRole(address _account, bytes32 _role) external onlyAdmin{
    bytes32 action_hash = keccak256(abi.encode(_account, _role, actionNonce-1));
    require(previous_action_hash == action_hash, "Invalid Hash");
    require(block.timestamp > action_queued[action_hash] + TIME_DELAY,
        "Not enough time has passed");
    // @audit missing to delete previous_action_hash;
    _setupRole(_role, _account);
    emit AddRole(_account, _role,  msg.sender);
}

function removeRole(address _account, bytes32 _role) external onlyAdmin{
    require(hasRole(_role, _account), "Address was not already specified role");
    _revokeRole(_role, _account);
    emit RemoveRole(_account, _role, msg.sender);
}
```
## Tool used

Manual Review

## Recommendation
```diff
function addRole(address _account, bytes32 _role) external onlyAdmin{
    bytes32 action_hash = keccak256(abi.encode(_account, _role, actionNonce-1));
    require(previous_action_hash == action_hash, "Invalid Hash");
    require(block.timestamp > action_queued[action_hash] + TIME_DELAY,
        "Not enough time has passed");
+    delete previous_action_hash; // @fix
    _setupRole(_role, _account);
    emit AddRole(_account, _role,  msg.sender);
}
```