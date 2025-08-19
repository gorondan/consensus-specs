from typing import List


class DelegatedValidator:
    delegators_balances: List[float]  # this mocks state.delegators[index]
    validator_balance: float  # this mocks state.balances[index]

    delegated_validator_quota: float
    delegators_quotas: List[float]
    delegated_balances: List[float]
    dry_delegated_balances: List[float]  # [dev] the amounts delegated over time, without any Rewards/Penalties
    validators_fees: List[float]
    total_delegated_balance: float
    fee_quotient: float

    def __init__(self):
        self.delegators_balances = []
        self.validator_balance = 0

        self.delegated_validator_quota = 0
        self.delegators_quotas = [0, 0, 0]
        self.delegated_balances = [0, 0, 0]

        self.dry_delegated_balances = [0, 0, 0]

        self.validators_fees = [0, 0, 0]
        self.total_delegated_balance = 0
        self.fee_quotient = 0.1

        self.setup_initial_values()

    def setup_initial_values(self) -> None:
        self.delegators_balances = [100, 100, 100]
        self.validator_balance = 32
        self.delegated_validator_quota = 1

    def recalculate_delegator_quotas(self) -> None:
        if self.total_delegated_balance == 0:
            self.delegated_validator_quota = 1
        else:
            self.delegated_validator_quota = (
                    self.validator_balance / (self.total_delegated_balance + self.validator_balance))
            for index in range(len(self.delegators_quotas)):
                self.delegators_quotas[index] = self.delegated_balances[index] / self.total_delegated_balance * (
                        1 - self.delegated_validator_quota)

    def delegate_to_validator(self, delegator_index: int, delegated_amount: float) -> None:
        # here we decrement the delegators available balance
        self.delegators_balances[delegator_index] -= delegated_amount
        self.dry_delegated_balances[delegator_index] += delegated_amount

        num_delegated_balances = len(self.delegated_balances)

        # ensure we have enough indexes inside the delegated validator to keep them parallel with delegator_index
        if (delegator_index > num_delegated_balances):
            for _ in range(delegator_index - num_delegated_balances):
                self.delegated_balances.append(0)
                self.delegated_quotas.append(0)

        # here we increase the delegated balance from this specific delegator, under this delegated validator, with delegated amount
        self.delegated_balances[delegator_index] += delegated_amount

        # here we increase the delegated validator's total delegated balance with delegated amount
        self.total_delegated_balance += delegated_amount

        # here we recalculate delegators' quotas under this delegated validator
        self.recalculate_delegator_quotas()

    def reward_delegated_validator(self, reward: float) -> None:
        validator_reward = self.delegated_validator_quota * reward

        # reward the operator
        self.validator_balance += validator_reward

        # reward the delegations
        self.apply_delegations_rewards(reward) # TO DO : update in specs the calculation of delegators reward as a quotas of the TOTAL reward

    def penalize_delegated_validator(self, penalty: float) -> None:
        validator_penalty = self.delegated_validator_quota * penalty

        # penalize the operator
        self.validator_balance -= validator_penalty

        # penalize the delegations
        self.apply_delegations_penalties(penalty) # TO DO : update in specs the calculation of delegators penalties as a quotas of the TOTAL penalty

    def apply_delegations_rewards(self, amount: float) -> None:
        self.total_delegated_balance += amount * (1- self.delegated_validator_quota) # Rewards are compounded in total delegated balance based on delegators total quota

        for index in range(len(self.delegators_quotas)):
            self.delegated_balances[index] += amount * self.delegators_quotas[index]
            self.validators_fees[index] += amount * self.delegators_quotas[index] * self.fee_quotient  # this was added for the patch

    def apply_delegations_penalties(self, amount: float) -> None:
        self.total_delegated_balance -= amount * (1- self.delegated_validator_quota) # Penalties are compounded in total delegated balance based on delegators total quota

        for index in range(len(self.delegators_quotas)):
            self.delegated_balances[index] -= amount * self.delegators_quotas[index]
            self.validators_fees[index] -= amount * self.delegators_quotas[index] * self.fee_quotient  # this was added for the patch

    # this assumes an empty exit queue
    def slash_pre(self, amount: float):
        validator_penalty = self.delegated_validator_quota * amount
        delegators_penalty = amount - validator_penalty

        self.validator_balance -= validator_penalty

        self.total_delegated_balance -= delegators_penalty

        # slash the delegated balances
        for index in range(len(self.delegated_balances)):
            self.delegated_balances[index] -= delegators_penalty * self.delegators_quotas[index]

    def slash_post(self, amount: float):

        validator_penalty = self.delegated_validator_quota * amount
        delegators_penalty = amount - validator_penalty

        self.validator_balance -= validator_penalty

        self.total_delegated_balance -= delegators_penalty

        # slash the delegated balances
        for index in range(len(self.delegated_balances)):
            self.delegated_balances[index] -= amount * self.delegators_quotas[index] # TO DO : update in specs the calculation of delegated balances as a quotas of the TOTAL slashing penalty

    # this is a naive implementation of the withdrawal, before this patch
    def withdraw_pre(self, delegator_index: float, amount: float):
        self.delegated_balances[delegator_index] -= amount
        self.total_delegated_balance -= amount

        validator_fee = amount * self.fee_quotient
        delegator_amount = amount - validator_fee

        self.delegators_balances[delegator_index] += delegator_amount
        self.validator_balance += validator_fee

        self.recalculate_delegator_quotas()
    '''
    This is equivalent to an undelegation
    '''
    def withdraw_post(self, delegator_index: float, amount: float):
        withdraw_from_validator_fee_ratio = amount / self.delegated_balances[delegator_index]
        self.delegated_balances[delegator_index] -= amount
        self.total_delegated_balance -= amount

        withdraw_from_validator_fee = self.validators_fees[delegator_index] * withdraw_from_validator_fee_ratio
        self.validators_fees[delegator_index] -= withdraw_from_validator_fee

        validator_fee = withdraw_from_validator_fee

        self.validator_balance += validator_fee
        self.delegators_balances[delegator_index] += amount - validator_fee

        self.recalculate_delegator_quotas()


class Simulator:
    dv: DelegatedValidator
    action_queue: List[List]

    def __init__(self, dv: DelegatedValidator):
        self.action_queue = []
        self.dv = dv

    def queue_action(self, action):
        self.action_queue.append(action)

    def simulate(self):
        print(chr(27) + "[2J")

        print("=====", "INITIAL", "=====")
        attrs = vars(self.dv)
        print('\n'.join("%s: %s" % item for item in attrs.items()))
        print('\n')

        for action in self.action_queue:
            print("=====", action[0], "=====")
            match len(action):  # this is the worst thing I've written, but it does what it needs to
                case 2:
                    action[1]()
                case 3:
                    action[1](action[2])
                case 4:
                    action[1](action[2], action[3])

            attrs = vars(self.dv)
            print('\n'.join("%s: %s" % item for item in attrs.items()))
            print('\n')

'''
Validator fee is what the Delegator owes to the Validator Operator in terms of staking rewards fees. 
It's deducted from the amount debited to the Delegator's non-delegated balance (the undelegated amount), during undelegation. 
It's constituted as a quotient out of the compounded rewards and penalties the validator has generated with the delegated stake of that particular delegator. 
Does not apply if compounded value (validators_fees[index]) is negative, nor does it apply to slashing.   
'''
dv = DelegatedValidator()
simulator = Simulator(dv)

simulator.queue_action(["Delegator 0 delegates 64", dv.delegate_to_validator, 0, 64])
simulator.queue_action(["Apply 0.5 reward", dv.reward_delegated_validator, 0.5])
simulator.queue_action(["Apply 0.3 reward", dv.reward_delegated_validator, 0.3])
simulator.queue_action(["Apply 0.1 reward", dv.reward_delegated_validator, 0.1])
simulator.queue_action(["Apply 0.1 penalty", dv.penalize_delegated_validator, 0.1])
# simulator.queue_action(["Apply 3 slashing/pre", dv.slash_pre, 3])
simulator.queue_action(["Apply 16 slashing/post", dv.slash_post, 16])
simulator.queue_action(["Perform withdraw/post for delegator index 0, amount 8", dv.withdraw_post, 0, 8])
simulator.simulate()
