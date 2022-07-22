(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (have_order)
        (maybe-have_order)
        (have_drink)
        (maybe-have_drink)
        (have_side)
        (maybe-have_side)
        (goal)
        (have-message)
        (force-statement)
        (forcing__ask-drink)
    )
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (maybe-have_order))
                (not (force-statement))
                (not (forcing__ask-drink))
            )
        :effect
            (labeled-oneof validate-response
                (outcome valid
                    (and
                        (have_order)
                        (not (maybe-have_order))
                        (forcing__ask-drink)
                    )
                )
                (outcome unclear
                    (and
                        (not (have_order))
                        (maybe-have_order)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action ask-drink
        :parameters()
        :precondition
            (and
                (have_order)
                (not (maybe-have_order))
                (not (have_drink))
                (not (maybe-have_drink))
                (not (force-statement))
            )
        :effect
            (labeled-oneof validate-response
                (outcome valid
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (forcing__ask-drink))
                    )
                )
                (outcome unclear
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action ask-side
        :parameters()
        :precondition
            (and
                (have_order)
                (not (maybe-have_order))
                (not (have_side))
                (not (maybe-have_side))
                (not (force-statement))
                (not (forcing__ask-drink))
            )
        :effect
            (labeled-oneof validate-side
                (outcome valid
                    (and
                        (have_side)
                        (not (maybe-have_side))
                        (goal)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action dialogue_statement
        :parameters()
        :precondition
            (and
                (have-message)
                (force-statement)
            )
        :effect
            (labeled-oneof reset
                (outcome lock
                    (and
                        (not (have-message))
                        (not (force-statement))
                    )
                )
            )
    )
    (:action clarify__ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (maybe-have_order)
                (not (force-statement))
                (not (forcing__ask-drink))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome deny
                    (and
                        (not (have_order))
                        (not (maybe-have_order))
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action clarify__ask-drink
        :parameters()
        :precondition
            (and
                (not (have_drink))
                (maybe-have_drink)
                (not (force-statement))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (forcing__ask-drink))
                    )
                )
                (outcome deny
                    (and
                        (not (have_drink))
                        (not (maybe-have_drink))
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
    (:action clarify__ask-side
        :parameters()
        :precondition
            (and
                (not (have_side))
                (maybe-have_side)
                (not (force-statement))
                (not (forcing__ask-drink))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome deny
                    (and
                        (not (have_side))
                        (not (maybe-have_side))
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (force-statement)
                    )
                )
            )
    )
)