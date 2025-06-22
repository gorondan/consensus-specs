class UndelegationExit:
    undelegated_amount = 0
    validator_fee_quotient = 0
    total_delegated_at_withdrawal = 0
    exit_epoch = 0

    def __init__(self, undelegated_amount, validator_fee_quotient, total_delegated_at_withdrawal, exit_epoch):
        self.undelegated_amount = undelegated_amount
        self.validator_fee_quotient = validator_fee_quotient
        self.total_delegated_at_withdrawal = total_delegated_at_withdrawal
        self.exit_epoch = exit_epoch

    def __repr__(self):
        return f"undelegated_amount:{self.undelegated_amount} validator_fee_quotient:{self.validator_fee_quotient} total_delegated_at_withdrawal:{self.total_delegated_at_withdrawal} | "

class Bla2:
    # this is state.balances[validator_index]
    validator_balance = 32
    exit_queue = []

    delegators_quotas = [0, 0, 0, 0]
    delegated_balances = [0, 0, 0, 0]

    delegated_validator_quota = 1
    total_delegated_balance = 0
    fee_quotient = 0.001

    def apply_delegation(self, delegator_index, amount):
        self.total_delegated_balance += amount
        self.delegated_balances[delegator_index] += amount
        pass

    def recalculate_quota(self):
        if self.total_delegated_balance == 0:
            self.delegated_validator_quota = 1
            self.delegators_quotas = [0, 0, 0, 0]
        else:
            self.delegated_validator_quota = (
                    self.validator_balance / (self.total_delegated_balance + self.validator_balance))
            for index in range(len(self.delegators_quotas)):
                self.delegators_quotas[index] = self.delegated_balances[index] / self.total_delegated_balance * (
                        1 - self.delegated_validator_quota)

    def apply_reward(self, amount):
        # in protocol
        validator_reward = self.delegated_validator_quota * amount

        # in protocol
        self.validator_balance += validator_reward

        # in BCA
        delegators_reward = amount - validator_reward

        # in BCA
        for index in range(len(self.delegators_quotas)):
            self.delegated_balances[index] += delegators_reward * self.delegators_quotas[index]
        pass

    def add_to_exit_queue(self, delegator_index, amount):
        print("delegator_index:",delegator_index, "undelegate:",amount )
        withdrawn_amount = amount
        validator_fee = self.fee_quotient * amount

        total_delegated_at_withdrawal = self.total_delegated_balance + self.validator_balance
        exit_epoch = 1234

        undelegated_amount = withdrawn_amount + validator_fee

        self.delegated_balances[delegator_index] -= undelegated_amount
        self.total_delegated_balance -= undelegated_amount


        self.recalculate_quota()

        self.exit_queue.append(
            UndelegationExit(undelegated_amount=undelegated_amount, validator_fee_quotient=self.fee_quotient,
                             total_delegated_at_withdrawal=total_delegated_at_withdrawal, exit_epoch=exit_epoch))

    def slash(self, total_slash):
        # I have to slash 4 eth from delegated + queued
        print("total_slash:", total_slash)

        # apply at every elem in exit_queue
        total_slashed_in_queue = 0


        for index in range(len(self.exit_queue)):
            exit_item = self.exit_queue[index]
            delegated_quota = exit_item.undelegated_amount / exit_item.total_delegated_at_withdrawal
            to_slash = delegated_quota * total_slash

            print("delegated_quota", delegated_quota)
            print("slashing index:", index, "with:", to_slash)

            total_slashed_in_queue+=to_slash

            self.exit_queue[index].undelegated_amount -= to_slash

        rest_to_slash = total_slash - total_slashed_in_queue

        validator_slash = self.delegated_validator_quota * rest_to_slash

        delegators_slash =  rest_to_slash - validator_slash

        print("---total_slashed_in_queue:", total_slashed_in_queue, "validator_slash:", validator_slash, "delegators_slash:", delegators_slash)



    def report(self):
        print('validator_balance ', self.validator_balance)
        print('delegators_quotas ', self.delegators_quotas)
        print('delegated_balances ', self.delegated_balances)
        print('delegated_validator_quota ', self.delegated_validator_quota)
        print('total_delegated_balance ', self.total_delegated_balance)
        print('undelegation_exit_queue ', self.exit_queue)
        print('------ ')

    def test_quota_1(self):
        sum = 0
        sum += self.delegated_validator_quota

        for index in range(len(self.delegators_quotas)):
            sum += self.delegators_quotas[index]

        print("Total quota in DV", sum)


bla = Bla2()

bla.apply_delegation(0, 20)
bla.apply_delegation(1, 20)
bla.recalculate_quota()
bla.report()

bla.add_to_exit_queue(0, 10) # ep 3
bla.add_to_exit_queue(1, 10) # ep 7
bla.apply_delegation(2, 20) # ep 9
bla.recalculate_quota()
bla.report()
bla.slash(8)  # ep 60
bla.report()
