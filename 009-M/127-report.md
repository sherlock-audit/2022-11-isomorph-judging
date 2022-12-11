ctf_sec

high

# lockVELO duration can be more than 4 years.

## Summary

The lockVELO() function allows users to lock VELO tokens for a specified duration, which can be longer than 4 years.

## Vulnerability Detail

the comment suggests:

>  @param _lockDuration time in seconds you wish to lock the tokens for, must be less than or equal to 4 years (4*365*24*60*60 = 126144000)

but there is no restriction on the lockDuration parameter in the code.

The lockVELO() function takes in two parameters: _tokenAmount and _lockDuration. The _lockDuration parameter specifies the time in seconds for which the VELO tokens will be locked, but there is no limit on this value. This means that users can lock their VELO tokens for longer than 4 years, which may not be intended.

## Impact

If users are able to lock their VELO tokens for longer than 4 years, it can potentially result in the tokens being locked for an extended period of time without the ability to be used or accessed. This can lead to financial losses and reduced flexibility in managing the tokens.

## Code Snippet

https://github.com/sherlock-audit/2022-11-isomorph/blob/main/contracts/Isomorph/contracts/Locker.sol#L58-L77

## Tool used

Manual Review

## Recommendation

It is recommended that the lockVELO() function be modified to include a maximum limit on the _lockDuration parameter. This will prevent users from locking their VELO tokens for longer than the intended maximum duration, and will ensure the flexibility and usability of the tokens. This can be achieved by adding a check to ensure that the _lockDuration value is less than or equal to the maximum allowed duration (e.g. 4 years).
