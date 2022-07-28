(define
    (domain order-pizza)
    (:requirements :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (have_pizza_flavour)
        (maybe-have_pizza_flavour)
        (have_drink)
        (maybe-have_drink)
        (have_side)
        (maybe-have_side)
        (goal)
        (have-message)
        (force-statement)
    )
    (:action force-all
        :parameters()
        :precondition
            (and
                (not (have_side))
                (not (have_pizza_flavour))
                (not (maybe-have_pizza_flavour))
                (not (have_drink))
                (not (maybe-have_drink))
                (not (maybe-have_side))
                (not (force-statement))
            )
        :effect
            (labeled-oneof validate
                (outcome valid
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (have_drink)
                        (not (maybe-have_drink))
                        (have_side)
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
    (:action complete
        :parameters()
        :precondition
            (and
                (have_side)
                (have_pizza_flavour)
                (not (maybe-have_pizza_flavour))
                (not (maybe-have_drink))
                (have_drink)
                (not (maybe-have_side))
            )
        :effect
            (labeled-oneof finish
                (outcome assign-goal
                    (and
                        (goal)
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
)