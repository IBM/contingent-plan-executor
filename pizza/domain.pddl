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
        (pizza_and_drink)
        (just_side)
        (maybe_pizza)
        (have-message)
        (force-statement)
    )
    (:action ask-pizza_flavour
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (have_side))
                (not (maybe-have_side))
                (not (maybe-have_pizza_flavour))
                (not (have_drink))
                (not (maybe-have_drink))
                (not (have_pizza_flavour))
            )
        :effect
            (labeled-oneof validate-slot-fill
                (outcome pizza_flavour_found-drink_found-side_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (have_drink)
                        (not (maybe-have_drink))
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome pizza_flavour_found-drink_found-side_maybe-found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome pizza_flavour_found-drink_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (have_drink)
                        (not (maybe-have_drink))
                        (pizza_and_drink)
                    )
                )
                (outcome pizza_flavour_found-drink_maybe-found-side_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (not (have_drink))
                        (maybe-have_drink)
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome pizza_flavour_found-drink_maybe-found-side_maybe-found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (not (have_drink))
                        (maybe-have_drink)
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome pizza_flavour_found-drink_maybe-found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome pizza_flavour_found-side_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome pizza_flavour_found-side_maybe-found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome pizza_flavour_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                    )
                )
                (outcome pizza_flavour_maybe-found-drink_found-side_found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (have_drink)
                        (not (maybe-have_drink))
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome pizza_flavour_maybe-found-drink_found-side_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome pizza_flavour_maybe-found-drink_found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome pizza_flavour_maybe-found-drink_maybe-found-side_found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (not (have_drink))
                        (maybe-have_drink)
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome pizza_flavour_maybe-found-drink_maybe-found-side_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (not (have_drink))
                        (maybe-have_drink)
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome pizza_flavour_maybe-found-drink_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome pizza_flavour_maybe-found-side_found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome pizza_flavour_maybe-found-side_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome pizza_flavour_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (maybe_pizza)
                    )
                )
                (outcome drink_found-side_found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome drink_found-side_maybe-found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome drink_found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome drink_maybe-found-side_found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                        (have_side)
                        (not (maybe-have_side))
                    )
                )
                (outcome drink_maybe-found-side_maybe-found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                        (not (have_side))
                        (maybe-have_side)
                    )
                )
                (outcome drink_maybe-found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                    )
                )
                (outcome side_found
                    (and
                        (have_side)
                        (not (maybe-have_side))
                        (just_side)
                    )
                )
                (outcome side_maybe-found
                    (and
                        (not (have_side))
                        (maybe-have_side)
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
                (not (maybe-have_side))
                (not (maybe-have_pizza_flavour))
                (have_pizza_flavour)
                (have_drink)
                (not (maybe-have_drink))
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
    (:action clarify__pizza_flavour
        :parameters()
        :precondition
            (and
                (not (have_pizza_flavour))
                (not (force-statement))
                (maybe-have_pizza_flavour)
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                    )
                )
                (outcome deny
                    (and
                        (not (have_pizza_flavour))
                        (not (maybe-have_pizza_flavour))
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
    (:action clarify__drink
        :parameters()
        :precondition
            (and
                (not (have_drink))
                (not (force-statement))
                (maybe-have_drink)
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome confirm
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
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
    (:action clarify__side
        :parameters()
        :precondition
            (and
                (not (have_side))
                (not (force-statement))
                (maybe-have_side)
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
    (:action single_slot__pizza_flavour
        :parameters()
        :precondition
            (and
                (not (have_pizza_flavour))
                (not (force-statement))
                (not (maybe-have_pizza_flavour))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome fill-slot
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                    )
                )
                (outcome slot-unclear
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (maybe_pizza)
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
    (:action single_slot__drink
        :parameters()
        :precondition
            (and
                (not (have_drink))
                (not (force-statement))
                (not (maybe-have_drink))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome fill-slot
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                    )
                )
                (outcome slot-unclear
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
    (:action single_slot__side
        :parameters()
        :precondition
            (and
                (not (have_side))
                (not (force-statement))
                (not (maybe-have_side))
            )
        :effect
            (labeled-oneof validate-clarification
                (outcome fill-slot
                    (and
                        (have_side)
                        (not (maybe-have_side))
                        (just_side)
                    )
                )
                (outcome slot-unclear
                    (and
                        (not (have_side))
                        (maybe-have_side)
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