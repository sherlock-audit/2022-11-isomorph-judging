GimelSec

medium

# The admin of `RoleControl` can use `DEFAULT_ADMIN_ROLE` to bypass the timelock

## Summary

In `RoleControl.sol`, only the admin can add a new role to an account. And that is a two step process with a time delay. However, the admin can add `DEFAULT_ADMIN_ROLE` to an account. Then, the account can add roles to any account without a time delay.

## Vulnerability Detail

The admin of `RoleControl` can add a new role to an account by calling `proposeAddRole()` and `addRole()`. It’s a two step process with a reasonable time delay. But a malicious admin can add `DEFAULT_ADMIN_ROLE` to an account he/she owns. Then, he/she can use that account to call `AccessControl.grantRole()` to immediately add roles.
https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/access/AccessControl.sol#L144


## Impact

The two step process with a time delay can be easily bypassed. It could cause serious problems. For example, a malicious admin can add `MINTER_ROLE` to an account immediately. Then he/she can arbitrarily mint tokens. Since the admin should be trustworthy, we consider it a medium issue.



## Code Snippet
https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/RoleControl.sol#L37

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/RoleControl.sol#L47

## Tool used

Manual Review

## Recommendation

There are many ways to fix the issue.

Block `DEFAULT_ADMIN_ROLE` in `proposeAddRole()` or override `AccessControl.grantRole`
