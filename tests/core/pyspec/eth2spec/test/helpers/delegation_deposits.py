from random import Random

from eth2spec.test.context import expect_assertion_error
from eth2spec.test.helpers.forks import is_post_altair, is_post_electra
from eth2spec.test.helpers.keys import pubkeys, privkeys
from eth2spec.test.helpers.state import get_delegator_balance
from eth2spec.test.helpers.epoch_processing import run_epoch_processing_to
from eth2spec.utils import bls
from eth2spec.utils.merkle_minimal import calc_merkle_tree_from_leaves, get_merkle_proof
from eth2spec.utils.ssz.ssz_impl import hash_tree_root
from eth2spec.utils.ssz.ssz_typing import List

def prepare_deposit_to_delegate_request(spec, delegator_index, amount,
                            index=None,
                            pubkey=None,
                            # privkey=None,
                            # withdrawal_credentials=None,
                            # signed=False
                                        ):
    """
    Create a deposit to delegate request for the given delegator, depositing the given amount.
    """
    if index is None:
        index = delegator_index

    if pubkey is None:
        pubkey = pubkeys[delegator_index]

    # if privkey is None:
    #     privkey = privkeys[delegator_index]

    # # insecurely use pubkey as withdrawal key if no credentials provided
    # if withdrawal_credentials is None:
    #     withdrawal_credentials = spec.BLS_WITHDRAWAL_PREFIX + spec.hash(pubkey)[1:]

    deposit_data = build_deposit_to_delegate_data(spec, pubkey, amount) #privkey, withdrawal_credentials, signed=signed
    return spec.DepositRequest(
        pubkey=deposit_data.pubkey,
        #withdrawal_credentials=deposit_data.withdrawal_credentials,
        amount=deposit_data.amount,
        #signature=deposit_data.signature,
        index=index
    )

def run_deposit_request_processing(
        spec,
        state,
        deposit_request,
        delegator_index,
        effective=True):

    """
    Run ``process_deposit_to_delegate_request``, yielding:
      - pre-state ('pre')
      - deposit_request ('deposit_request')
      - post-state ('post').
    """
    assert is_post_electra(spec)

    pre_delegator_count = len(state.delegators)
    pre_delegator_balance = 0
    is_delegator_top_up = False
    # is a delegator balance top-up
    if delegator_index < pre_delegator_count:
        is_delegator_top_up = True
        pre_balance = get_delegator_balance(state, delegator_index)
        pre_effective_delegated_balance = state.delegators[delegator_index].effective_delegated_balance

    yield 'pre', state
    yield 'deposit_request', deposit_request

    spec.process_deposit_request(state, deposit_request)

    yield 'post', state

    # New validator is only created after the pending_deposits processing
    assert len(state.delegators) == pre_delegator_count
    assert len(state.delegators_balances) == pre_delegator_count

    if is_delegator_top_up:
        assert state.delegators[delegator_index].effective_delegated_balance == pre_effective_delegated_balance
        assert state.state.delegators_balances[delegator_index] == pre_balance

    pending_deposit = spec.PendingDeposit(
        pubkey=deposit_request.pubkey,
        withdrawal_credentials=deposit_request.withdrawal_credentials,
        amount=deposit_request.amount,
        signature=deposit_request.signature,
        slot=state.slot,
    )

    assert state.pending_deposits == [pending_deposit]