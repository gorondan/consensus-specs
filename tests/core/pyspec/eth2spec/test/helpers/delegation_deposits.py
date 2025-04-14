from eth2spec.test.helpers.forks import is_post_electra
from eth2spec.test.helpers.keys import pubkeys, privkeys
from eth2spec.test.helpers.state import get_delegator_balance
from eth2spec.utils import bls

def run_add_new_delegator(spec, state, pubkey, privkey, amount):
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


def sign_deposit_to_delegate_message(spec, deposit_to_delegate_message, privkey, fork_version=None):
    if fork_version is not None:
        domain = spec.compute_domain(domain_type=spec.DOMAIN_DEPOSIT_TO_DELEGATE, fork_version=fork_version)
    else:
        domain = spec.compute_domain(spec.DOMAIN_DEPOSIT_TO_DELEGATE)
    signing_root = spec.compute_signing_root(deposit_to_delegate_message, domain)

    return spec.DepositToDelegateRequest(
        pubkey=deposit_to_delegate_message.pubkey,
        withdrawal_credentials=deposit_to_delegate_message.withdrawal_credentials,
        amount=deposit_to_delegate_message.amount,
        signature=bls.Sign(privkey, signing_root)
    )
