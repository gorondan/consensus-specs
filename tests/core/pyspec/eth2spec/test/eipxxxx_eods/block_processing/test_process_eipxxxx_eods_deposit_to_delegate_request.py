from eth2spec.test.context import spec_state_test, expect_assertion_error, \
    with_eipxxxx_eods_and_later

def empty_block(spec):
    return spec.BeaconBlock()

def run_process_whisk_opening_proof(spec, state, block, valid=True):
    yield 'pre', state
    yield 'block', block

    if not valid:
        expect_assertion_error(lambda: spec.process_whisk_opening_proof(state, block))
        yield 'post', None
        return

    spec.process_whisk_opening_proof(state, block)

    yield 'post', state


@with_eipxxxx_eods_and_later
@spec_state_test
def test_deposit_to_delegate_no_delegator_available(spec, state):
    print(spec)
    print(state)
    assert 1 > 1
