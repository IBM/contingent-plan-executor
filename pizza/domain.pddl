(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (have_order)
        (maybe-have_order)
        (goal)
        (have-message)
        (force-statement)
    )
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (not (force-statement))
                (not (maybe-have_order))
            )
        :effect
            (labeled-oneof validate-slot-fill
                (outcome order_certain
                    (and
                        (have_order)
                        (not (maybe-have_order))
                    )
                )
                (outcome order_uncertain
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
    (:action complete
        :parameters()
        :precondition
            (and
                (have_order)
                (not (force-statement))
                (not (maybe-have_order))
            )
        :effect
            (labeled-oneof finish
                (outcome assign-goal
                    (and
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
                (force-statement)
                (have-message)
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
    (:action clarify__order
        :parameters()
        :precondition
            (and
                (not (have_order))
                (maybe-have_order)
                (not (force-statement))
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
)