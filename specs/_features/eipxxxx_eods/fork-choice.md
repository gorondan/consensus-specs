# eipxxxx_eods -- Fork Choice

<!-- mdformat-toc start --slug=github --no-anchors --maxlevel=6 --minlevel=2 -->

- [Introduction](#introduction)
- [Helpers](#helpers)
  - [Modified `PayloadAttributes`](#modified-payloadattributes)

<!-- mdformat-toc end -->

## Introduction

This is the modification of the fork choice according to the eipxxxx_eods proposed upgrade.

Unless stated explicitly, all prior functionality from
[Bellatrix](../bellatrix/fork-choice.md) is inherited.


## Helpers

### Modified `PayloadAttributes`

`PayloadAttributes` is extended with the `withdrawals_from_delegate` field.

```python
@dataclass
class PayloadAttributes(object):
    timestamp: uint64
    prev_randao: Bytes32
    suggested_fee_recipient: ExecutionAddress
    withdrawals: Sequence[Withdrawal]  
    withdrawals_from_delegators: Sequence[WithdrawalFromDelegators]  # [New in eipxxxx_eods]
```
