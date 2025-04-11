from eth2spec.test.helpers.forks import is_post_electra
from eth2spec.test.helpers.keys import pubkeys, privkeys
from eth2spec.test.helpers.state import get_delegator_balance
from eth2spec.utils import bls


def prepare_deposit_to_delegate_request(spec, delegator_index, amount,
                            index=None,
                            pubkey=None,
                            privkey=None,
                            withdrawal_credentials=None,
                            signed=False
                                        ):
    """
    Create a deposit to delegate request for the given delegator, depositing the given amount.
    """
    if index is None:
        index = delegator_index

    if pubkey is None:
        pubkey = pubkeys[delegator_index]

    if privkey is None:
        privkey = privkeys[delegator_index]

    # insecurely use pubkey as withdrawal key if no credentials provided
    if withdrawal_credentials is None:
        withdrawal_credentials = spec.BLS_WITHDRAWAL_PREFIX + spec.hash(pubkey)[1:]

    deposit_to_delegate_data = build_deposit_to_delegate_data(spec, pubkey, privkey, amount, withdrawal_credentials, signed=signed)
    return spec.DepositToDelegateRequest(
        pubkey=deposit_to_delegate_data.pubkey,
        withdrawal_credentials=deposit_to_delegate_data.withdrawal_credentials,
        amount=deposit_to_delegate_data.amount,
        signature=deposit_to_delegate_data.signature,
        index=index
    )

def build_deposit_to_delegate_data(spec, pubkey, privkey, amount, withdrawal_credentials, fork_version=None, signed=False):
    deposit_to_delegate_data = spec.DepositToDelegateData(
        pubkey=pubkey,
        withdrawal_credentials=withdrawal_credentials,
        amount=amount,
    )
    if signed:
        sign_deposit_to_delegate_data(spec, deposit_to_delegate_data, privkey, fork_version)
    return deposit_to_delegate_data

def sign_deposit_to_delegate_data(spec, deposit_to_delegate_data, privkey, fork_version=None):
    deposit_to_delegate_message = spec.DepositToDelegateMessage(
        pubkey=deposit_to_delegate_data.pubkey,
        withdrawal_credentials=deposit_to_delegate_data.withdrawal_credentials,
        amount=deposit_to_delegate_data.amount)
    if fork_version is not None:
        domain = spec.compute_domain(domain_type=spec.DOMAIN_DEPOSIT_TO_DELEGATE, fork_version=fork_version)
    else:
        domain = spec.compute_domain(spec.DOMAIN_DEPOSIT_TO_DELEGATE)
    signing_root = spec.compute_signing_root(deposit_to_delegate_message, domain)
    deposit_to_delegate_data.signature = bls.Sign(privkey, signing_root)

def run_deposit_to_delegate_request_processing(
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

    spec.process_deposit_request(state, deposit_request)

    # New delegator is created only after processing the deposit_to_delegate
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