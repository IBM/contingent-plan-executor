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
        (allow_single_slot_side)
        (allow_single_slot_drink)
        (allow_single_slot_pizza_flavour)
    )
    (:action complete
        :parameters()
        :precondition
            (and
                (have_side)
                (have_pizza_flavour)
                (not (maybe-have_side))
                (not (maybe-have_drink))
                (have_drink)
                (not (maybe-have_pizza_flavour))
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
    (:action ask-order
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (maybe-have_side))
                (not (maybe-have_drink))
                (not (have_side))
                (not (have_pizza_flavour))
                (not (have_drink))
                (not (maybe-have_pizza_flavour))
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
                        (allow_single_slot_side)
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
                        (allow_single_slot_side)
                    )
                )
                (outcome pizza_flavour_found-side_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (have_side)
                        (not (maybe-have_side))
                        (allow_single_slot_drink)
                    )
                )
                (outcome pizza_flavour_found-side_maybe-found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (not (have_side))
                        (maybe-have_side)
                        (allow_single_slot_drink)
                    )
                )
                (outcome pizza_flavour_found
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (allow_single_slot_drink)
                        (allow_single_slot_side)
                        (have-message)
                        (force-statement)
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
                        (allow_single_slot_side)
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
                        (allow_single_slot_side)
                    )
                )
                (outcome pizza_flavour_maybe-found-side_found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (have_side)
                        (not (maybe-have_side))
                        (allow_single_slot_drink)
                    )
                )
                (outcome pizza_flavour_maybe-found-side_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (not (have_side))
                        (maybe-have_side)
                        (allow_single_slot_drink)
                    )
                )
                (outcome pizza_flavour_maybe-found
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
                        (maybe_pizza)
                        (allow_single_slot_drink)
                        (allow_single_slot_side)
                    )
                )
                (outcome drink_found-side_found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (have_side)
                        (not (maybe-have_side))
                        (allow_single_slot_pizza_flavour)
                    )
                )
                (outcome drink_found-side_maybe-found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (have_side))
                        (maybe-have_side)
                        (allow_single_slot_pizza_flavour)
                    )
                )
                (outcome drink_found
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (allow_single_slot_pizza_flavour)
                        (allow_single_slot_side)
                        (have-message)
                        (force-statement)
                    )
                )
                (outcome drink_maybe-found-side_found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                        (have_side)
                        (not (maybe-have_side))
                        (allow_single_slot_pizza_flavour)
                    )
                )
                (outcome drink_maybe-found-side_maybe-found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                        (not (have_side))
                        (maybe-have_side)
                        (allow_single_slot_pizza_flavour)
                    )
                )
                (outcome drink_maybe-found
                    (and
                        (not (have_drink))
                        (maybe-have_drink)
                        (allow_single_slot_pizza_flavour)
                        (allow_single_slot_side)
                    )
                )
                (outcome side_found
                    (and
                        (have_side)
                        (not (maybe-have_side))
                        (allow_single_slot_pizza_flavour)
                        (allow_single_slot_drink)
                        (have-message)
                        (force-statement)
                    )
                )
                (outcome side_maybe-found
                    (and
                        (not (have_side))
                        (maybe-have_side)
                        (allow_single_slot_pizza_flavour)
                        (allow_single_slot_drink)
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
                (not (maybe-have_side))
                (not (force-statement))
                (allow_single_slot_side)
            )
        :effect
            (labeled-oneof validate-slot-fill
                (outcome fill-slot
                    (and
                        (have_side)
                        (not (maybe-have_side))
                        (not (allow_single_slot_side))
                        (have-message)
                        (force-statement)
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
    (:action single_slot__drink
        :parameters()
        :precondition
            (and
                (not (maybe-have_drink))
                (allow_single_slot_drink)
                (not (force-statement))
                (not (have_drink))
            )
        :effect
            (labeled-oneof validate-slot-fill
                (outcome fill-slot
                    (and
                        (have_drink)
                        (not (maybe-have_drink))
                        (not (allow_single_slot_drink))
                        (have-message)
                        (force-statement)
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
    (:action single_slot__pizza_flavour
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (have_pizza_flavour))
                (allow_single_slot_pizza_flavour)
                (not (maybe-have_pizza_flavour))
            )
        :effect
            (labeled-oneof validate-slot-fill
                (outcome fill-slot
                    (and
                        (have_pizza_flavour)
                        (not (maybe-have_pizza_flavour))
                        (not (allow_single_slot_pizza_flavour))
                        (have-message)
                        (force-statement)
                    )
                )
                (outcome slot-unclear
                    (and
                        (not (have_pizza_flavour))
                        (maybe-have_pizza_flavour)
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
    (:action clarify__pizza_flavour
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (maybe-have_pizza_flavour)
                (not (have_pizza_flavour))
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
                        (allow_single_slot_pizza_flavour)
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
                (not (force-statement))
                (maybe-have_drink)
                (not (have_drink))
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
                        (allow_single_slot_drink)
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
                (maybe-have_side)
                (not (force-statement))
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
                        (allow_single_slot_side)
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