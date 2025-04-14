from build.lib.eth2spec.eipxxxx_eods.mainnet import MIN_DEPOSIT_TO_DELEGATE_AMOUNT, \
    MAX_PER_EPOCH_DEPOSITS_TO_DELEGATE_PROCESSING_LIMIT
from build.lib.eth2spec.test.helpers.keys import pubkeys, privkeys
from eth2spec.test.context import spec_state_test, expect_assertion_error, \
    with_eipxxxx_eods_and_later
from eth2spec.test.helpers.delegation_deposits import sign_deposit_to_delegate_message, run_add_new_delegator



@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_creates_delegator_if_needed(spec, state):
    initial_delegators_len = len(state.delegators)

    pubkey = pubkeys[1]
    privkey = privkeys[1]
    amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT
    withdrawal_credentials = (
            spec.COMPOUNDING_WITHDRAWAL_PREFIX
            + b'\x00' * 11  # specified 0s
            + b'\x59' * 20  # a 20-byte eth1 address
    )

    # this is a mock of EL message
    deposit_to_delegate_message = spec.DepositToDelegateMessage(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        amount=amount,
    )

    deposit_to_delegate_request = sign_deposit_to_delegate_message(spec, deposit_to_delegate_message, privkey)
    spec.process_deposit_to_delegate_request(state, deposit_to_delegate_request)
    spec.process_pending_deposits_to_delegate(state)

    assert len(state.delegators) == initial_delegators_len + 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_does_top_up_if_needed(spec, state):
    pubkey = pubkeys[1]
    privkey = privkeys[1]
    existing_delegator_amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT
    run_add_new_delegator(spec, state, pubkey, privkey, existing_delegator_amount)

    pre_topup_number_of_delegators = len(state.delegators)

    topup_amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT

    withdrawal_credentials = (
            spec.COMPOUNDING_WITHDRAWAL_PREFIX
            + b'\x00' * 11  # specified 0s
            + b'\x59' * 20  # a 20-byte eth1 address
    )
    # this is a mock of a NEW EL message
    deposit_to_delegate_message = spec.DepositToDelegateMessage(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        amount=topup_amount,
    )

    deposit_to_delegate_request = sign_deposit_to_delegate_message(spec, deposit_to_delegate_message, privkey)
    spec.process_deposit_to_delegate_request(state, deposit_to_delegate_request)
    spec.process_pending_deposits_to_delegate(state)

    assert len(state.delegators) == pre_topup_number_of_delegators
    assert state.delegators_balances[0] == 2 * spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_request_respects_max_processing_limit_value(spec, state):
    extra_deposits = 100

    for i in range(spec.MAX_PER_EPOCH_DEPOSITS_TO_DELEGATE_PROCESSING_LIMIT + extra_deposits):
        pubkey = pubkeys[i]
        privkey = privkeys[i]
        amount = spec.MIN_DEPOSIT_TO_DELEGATE_AMOUNT
        withdrawal_credentials = (
                spec.COMPOUNDING_WITHDRAWAL_PREFIX
                + b'\x00' * 11  # specified 0s
                + b'\x59' * 20  # a 20-byte eth1 address
        )
        # this is a mock of EL message
        deposit_to_delegate_message = spec.DepositToDelegateMessage(
            pubkey=pubkey,
            withdrawal_credentials=withdrawal_credentials,
            amount=amount,
        )

        deposit_to_delegate_request = sign_deposit_to_delegate_message(spec, deposit_to_delegate_message, privkey)
        spec.process_deposit_to_delegate_request(state, deposit_to_delegate_request)

    spec.process_pending_deposits_to_delegate(state)

    assert len(state.delegators) <= spec.MAX_PER_EPOCH_DEPOSITS_TO_DELEGATE_PROCESSING_LIMIT
    assert len(state.pending_deposits_to_delegate) == extra_deposits


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_unable_to_withdraw_before_withdrawable_epoch(spec, state):
    assert 1 > 1


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_can_withdraw_after_withdrawable_epoch(spec, state):
    assert 1 > 1
