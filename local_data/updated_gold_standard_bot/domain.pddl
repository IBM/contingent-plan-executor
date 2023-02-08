(define
    (domain day-planner)
    (:requirements         :strips :typing)
    (:types )
    (:constants )
    (:predicates
        (know__location)
        (know__phone_number)
        (maybe-know__phone_number)
        (know__cuisine)
        (maybe-know__cuisine)
        (know__have_allergy)
        (have_allergy)
        (know__food_restriction)
        (know__budget)
        (know__outing_type)
        (maybe-know__outing_type)
        (know__conflict)
        (conflict)
        (know__restaurant)
        (know__outing)
        (know__goal)
        (goal)
        (have-message)
        (force-statement)
        (allow_single_slot_outing_type)
        (allow_single_slot_budget)
        (forcing__get-allergy)
    )
    (:action get-have-allergy
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (forcing__get-allergy))
                (not (know__have_allergy))
            )
        :effect
            (labeled-oneof         get-have-allergy__set-allergy
                (outcome indicate_allergy
                    (and
                        (forcing__get-allergy)
                        (know__have_allergy)
                        (have_allergy)
                    )
                )
                (outcome indicate_no_allergy
                    (and
                        (know__conflict)
                        (know__have_allergy)
                        (not (have_allergy))
                        (not (conflict))
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
    (:action get-allergy
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (know__have_allergy)
                (have_allergy)
            )
        :effect
            (labeled-oneof         get-allergy__set-allergy
                (outcome update_allergy
                    (and
                        (not (forcing__get-allergy))
                        (know__food_restriction)
                    )
                )
                (outcome fallback
                    (and
                        (have-message)
                        (not (forcing__get-allergy))
                        (force-statement)
                    )
                )
            )
    )
    (:action check-conflicts
        :parameters()
        :precondition
            (and
                (know__cuisine)
                (know__have_allergy)
                (have_allergy)
                (not (know__conflict))
                (know__food_restriction)
                (not (maybe-know__cuisine))
                (not (forcing__get-allergy))
                (not (force-statement))
                (know__location)
            )
        :effect
            (labeled-oneof         check-conflicts__check-conflicts
                (outcome restriction-dessert
                    (and
                        (know__conflict)
                        (conflict)
                    )
                )
                (outcome restriction-mexican
                    (and
                        (know__conflict)
                        (conflict)
                    )
                )
                (outcome no-restriction-1
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
                (outcome no-restriction-2
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
                (outcome no-restriction-3
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
                (outcome no-restriction-4
                    (and
                        (know__conflict)
                        (not (conflict))
                    )
                )
            )
    )
    (:action reset-preferences
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (know__conflict)
                (conflict)
                (not (forcing__get-allergy))
            )
        :effect
            (labeled-oneof         reset-preferences__reset
                (outcome reset-values
                    (and
                        (not (know__have_allergy))
                        (not (know__food_restriction))
                        (have-message)
                        (not (know__cuisine))
                        (not (know__conflict))
                        (force-statement)
                        (not (maybe-know__cuisine))
                    )
                )
            )
    )
    (:action set-restaurant
        :parameters()
        :precondition
            (and
                (know__cuisine)
                (not (know__restaurant))
                (know__conflict)
                (not (forcing__get-allergy))
                (not (maybe-know__cuisine))
                (not (force-statement))
                (not (conflict))
            )
        :effect
            (labeled-oneof         set-restaurant__assign_restaurant
                (outcome set-mexican
                    (and
                        (know__restaurant)
                    )
                )
                (outcome set-italian
                    (and
                        (know__restaurant)
                    )
                )
                (outcome set-chinese
                    (and
                        (know__restaurant)
                    )
                )
                (outcome set-dessert
                    (and
                        (know__restaurant)
                    )
                )
            )
    )
    (:action set-outing
        :parameters()
        :precondition
            (and
                (know__budget)
                (not (maybe-know__outing_type))
                (know__outing_type)
                (not (forcing__get-allergy))
                (not (force-statement))
            )
        :effect
            (labeled-oneof         set-outing__assign_outing
                (outcome set-club
                    (and
                        (know__outing)
                    )
                )
                (outcome set-library
                    (and
                        (know__outing)
                    )
                )
                (outcome set-theater
                    (and
                        (know__outing)
                    )
                )
                (outcome set-golf
                    (and
                        (know__outing)
                    )
                )
            )
    )
    (:action complete
        :parameters()
        :precondition
            (and
                (know__outing)
                (know__restaurant)
                (not (forcing__get-allergy))
                (not (maybe-know__phone_number))
                (know__phone_number)
                (not (force-statement))
                (know__location)
            )
        :effect
            (labeled-oneof         complete__finish
                (outcome finish
                    (and
                        (know__goal)
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
            (labeled-oneof         dialogue_statement__reset
                (outcome lock
                    (and
                        (not (force-statement))
                        (not (have-message))
                    )
                )
            )
    )
    (:action slot-fill__get-location
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (know__location))
                (not (forcing__get-allergy))
            )
        :effect
            (labeled-oneof         slot-fill__get-location__validate-slot-fill
                (outcome location_found
                    (and
                        (have-message)
                        (force-statement)
                        (know__location)
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
    (:action slot-fill__get-phone_number
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (know__phone_number))
                (not (forcing__get-allergy))
                (not (maybe-know__phone_number))
            )
        :effect
            (labeled-oneof         slot-fill__get-phone_number__validate-slot-fill
                (outcome phone_number_found
                    (and
                        (know__phone_number)
                        (not (maybe-know__phone_number))
                    )
                )
                (outcome phone_number_maybe-found
                    (and
                        (maybe-know__phone_number)
                        (not (know__phone_number))
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
    (:action clarify__phone_number
        :parameters()
        :precondition
            (and
                (maybe-know__phone_number)
                (not (know__phone_number))
                (not (force-statement))
                (not (forcing__get-allergy))
            )
        :effect
            (labeled-oneof         clarify__phone_number__validate-clarification
                (outcome confirm
                    (and
                        (know__phone_number)
                        (not (maybe-know__phone_number))
                    )
                )
                (outcome deny
                    (and
                        (not (know__phone_number))
                        (not (maybe-know__phone_number))
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
    (:action slot-fill__get-cuisine
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (not (forcing__get-allergy))
                (not (know__cuisine))
                (not (maybe-know__cuisine))
            )
        :effect
            (labeled-oneof         slot-fill__get-cuisine__validate-slot-fill
                (outcome cuisine_found
                    (and
                        (not (maybe-know__cuisine))
                        (have-message)
                        (force-statement)
                        (know__cuisine)
                    )
                )
                (outcome cuisine_maybe-found
                    (and
                        (maybe-know__cuisine)
                        (not (know__cuisine))
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
    (:action clarify__cuisine
        :parameters()
        :precondition
            (and
                (not (force-statement))
                (maybe-know__cuisine)
                (not (forcing__get-allergy))
                (not (know__cuisine))
            )
        :effect
            (labeled-oneof         clarify__cuisine__validate-clarification
                (outcome confirm
                    (and
                        (not (maybe-know__cuisine))
                        (know__cuisine)
                    )
                )
                (outcome deny
                    (and
                        (not (know__cuisine))
                        (not (maybe-know__cuisine))
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
    (:action slot-fill__get_outing
        :parameters()
        :precondition
            (and
                (not (know__budget))
                (not (maybe-know__outing_type))
                (not (forcing__get-allergy))
                (not (know__outing_type))
                (not (force-statement))
            )
        :effect
            (labeled-oneof         slot-fill__get_outing__validate-slot-fill
                (outcome budget_found-outing_type_found
                    (and
                        (know__outing_type)
                        (not (maybe-know__outing_type))
                        (know__budget)
                    )
                )
                (outcome budget_found-outing_type_maybe-found
                    (and
                        (maybe-know__outing_type)
                        (not (know__outing_type))
                        (know__budget)
                    )
                )
                (outcome budget_found
                    (and
                        (have-message)
                        (allow_single_slot_outing_type)
                        (force-statement)
                        (know__budget)
                    )
                )
                (outcome outing_type_found
                    (and
                        (have-message)
                        (not (maybe-know__outing_type))
                        (allow_single_slot_budget)
                        (know__outing_type)
                        (force-statement)
                    )
                )
                (outcome outing_type_maybe-found
                    (and
                        (maybe-know__outing_type)
                        (not (know__outing_type))
                        (allow_single_slot_budget)
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
    (:action single_slot__outing_type
        :parameters()
        :precondition
            (and
                (not (maybe-know__outing_type))
                (not (forcing__get-allergy))
                (not (know__outing_type))
                (allow_single_slot_outing_type)
                (not (force-statement))
            )
        :effect
            (labeled-oneof         single_slot__outing_type__validate-slot-fill
                (outcome fill-slot
                    (and
                        (know__outing_type)
                        (not (maybe-know__outing_type))
                        (not (allow_single_slot_outing_type))
                    )
                )
                (outcome slot-unclear
                    (and
                        (maybe-know__outing_type)
                        (not (know__outing_type))
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
    (:action single_slot__budget
        :parameters()
        :precondition
            (and
                (allow_single_slot_budget)
                (not (force-statement))
                (not (know__budget))
                (not (forcing__get-allergy))
            )
        :effect
            (labeled-oneof         single_slot__budget__validate-slot-fill
                (outcome fill-slot
                    (and
                        (not (allow_single_slot_budget))
                        (know__budget)
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
    (:action clarify__outing_type
        :parameters()
        :precondition
            (and
                (maybe-know__outing_type)
                (not (force-statement))
                (not (know__outing_type))
                (not (forcing__get-allergy))
            )
        :effect
            (labeled-oneof         clarify__outing_type__validate-clarification
                (outcome confirm
                    (and
                        (know__outing_type)
                        (not (maybe-know__outing_type))
                    )
                )
                (outcome deny
                    (and
                        (not (know__outing_type))
                        (not (maybe-know__outing_type))
                        (allow_single_slot_outing_type)
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