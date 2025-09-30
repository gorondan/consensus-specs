pragma solidity ^0.8.20;

contract DelegationOperationsContract {
    /// @notice Unified event, carrying the DelegationOperationRequest fields. This will be used for all operation types.
    event DelegationOperationRequest(
        bytes1 opType,
        bytes source_pubkey,
        bytes target_pubkey,
        uint64 amount,
        address execution_address
    );

    // Operation types
    bytes1 constant ACTIVATE_OPERATOR = 0x01;
    bytes1 constant DELEGATE = 0x02;
    bytes1 constant UNDELEGATE = 0x03;
    bytes1 constant REDELEGATE = 0x04;
    bytes1 constant WITHDRAW_FROM_DELEGATOR = 0x05;

    function activateOperator(bytes calldata validator_pubkey) external {
        require(validator_pubkey.length == 48, "DelegationOperationsContract: Invalid pubkey");
        emit DelegationOperationRequest(
            ACTIVATE_OPERATOR,
            new bytes(0), // no source
            validator_pubkey,
            0, // no amount
            msg.sender
        );
    }

    function delegate(bytes calldata validator_pubkey, uint64 amount) external {
        require(validator_pubkey.length == 48, "DelegationOperationsContract: Invalid pubkey");
        require(amount > 0, "DelegationOperationsContract: Amount must be > 0");
        emit DelegationOperationRequest(
            DELEGATE,
            new bytes(0), // no source
            validator_pubkey,
            amount,
            msg.sender
        );
    }

    function undelegate(bytes calldata validator_pubkey, uint64 amount) external {
        require(validator_pubkey.length == 48, "DelegationOperationsContract: Invalid pubkey");
        require(amount > 0, "DelegationOperationsContract: Amount must be > 0");
        emit DelegationOperationRequest(
            UNDELEGATE,
            new bytes(0), // no source
            validator_pubkey,
            amount,
            msg.sender
        );
    }

    function redelegate(
        bytes calldata from_validator_pubkey,
        bytes calldata to_validator_pubkey,
        uint64 amount
    ) external {
        require(from_validator_pubkey.length == 48, "DelegationOperationsContract: Invalid pubkey");
        require(to_validator_pubkey.length == 48, "DelegationOperationsContract: Invalid pubkey");
        require(amount > 0, "DelegationOperationsContract: Amount must be > 0");
        emit DelegationOperationRequest(
            REDELEGATE,
            from_validator_pubkey,
            to_validator_pubkey,
            amount,
            msg.sender
        );
    }

    function withdrawFromDelegator(uint64 amount) external {
        require(amount > 0, "DelegationOperationsContract: Amount must be > 0");
        emit DelegationOperationRequest(
            WITHDRAW_FROM_DELEGATOR,
            new bytes(0),
            new bytes(0),
            amount,
            msg.sender
        );
    }
}
