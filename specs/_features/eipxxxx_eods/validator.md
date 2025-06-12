
#### Modified Execution Requests

1. The execution payload is obtained from the execution engine as defined above using `payload_id`. The response also includes a `execution_requests` entry containing a list of bytes. Each element on the list corresponds to one SSZ list of requests as defined in [EIP-7685](https://eips.ethereum.org/EIPS/eip-7685). The first byte of each request is used to determine the request type. Requests must be ordered by request type in ascending order. As a result, there can only be at most one instance of each request type.
2. Set `block.body.execution_requests = get_execution_requests(execution_requests)`, where:

```python
def get_execution_requests(execution_requests_list: Sequence[bytes]) -> ExecutionRequests:
    deposits = []
    withdrawals = []
    consolidations = []
    delegation_operations = []

    request_types = [
        DEPOSIT_REQUEST_TYPE,
        WITHDRAWAL_REQUEST_TYPE,
        CONSOLIDATION_REQUEST_TYPE,
        DELEGATION_OPERATION_REQUEST_TYPE
    ]

    prev_request_type = None
    for request in execution_requests_list:
        request_type, request_data = request[0:1], request[1:]

        # Check that the request type is valid
        assert request_type in request_types
        # Check that the request data is not empty
        assert len(request_data) != 0
        # Check that requests are in strictly ascending order
        # Each successive type must be greater than the last with no duplicates
        assert prev_request_type is None or prev_request_type < request_type
        prev_request_type = request_type

        if request_type == DEPOSIT_REQUEST_TYPE:
            deposits = ssz_deserialize(
                List[DepositRequest, MAX_DEPOSIT_REQUESTS_PER_PAYLOAD],
                request_data
            )
        elif request_type == WITHDRAWAL_REQUEST_TYPE:
            withdrawals = ssz_deserialize(
                List[WithdrawalRequest, MAX_WITHDRAWAL_REQUESTS_PER_PAYLOAD],
                request_data
            )
        elif request_type == CONSOLIDATION_REQUEST_TYPE:
            consolidations = ssz_deserialize(
                List[ConsolidationRequest, MAX_CONSOLIDATION_REQUESTS_PER_PAYLOAD],
                request_data
            )
        elif request_type == DELEGATION_OPERATION_REQUEST_TYPE:
            delegation_operations = ssz_deserialize(
                List[DelegationOperationRequest, MAX_DELEGATION_OPERATIONS_REQUESTS_PER_PAYLOAD],
                request_data
            )    

    return ExecutionRequests(
        deposits=deposits,
        withdrawals=withdrawals,
        consolidations=consolidations,
        delegation_operations=delegation_operations
    )
```
