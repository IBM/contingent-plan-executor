import re

from hovor.outcome_determiners.unified_workspace_outcome_determiner import UnifiedWorkspaceOutcomeDeterminer
from hovor.outcome_determiners.workspace_outcome_determiner import WorkspaceOutcomeDeterminer


class RegexWorkspaceOutcomeDeterminer(UnifiedWorkspaceOutcomeDeterminer):
    def configuration(self, action_name, name, intents, entities):
        masked_intents = self._mask_intents(intents)

        self._regex_providers = {}
        for intent, utterances in intents.items():
            self._regex_providers[intent] = self._parse_value_providers(utterances)

        return super(RegexWorkspaceOutcomeDeterminer, self).configuration(action_name, name, masked_intents, entities)

    def _report_entities(self, response, progress):
        super()._report_entities(response, progress)

        for intent_info in response['intents']:
            intent = intent_info["intent"]

            for provider in self._regex_providers.get(intent, []):
                updates = provider(progress.action_result.get_field("input"))
                for entity_name, entity_value in updates.items():
                    progress.add_detected_entity(entity_name, entity_value)

    def _parse_value_providers(self, utterances):
        value_providers = []
        for utterance in utterances:
            value_provider = self._parse_value_provider(utterance)
            value_providers.append(value_provider)

        return value_providers

    def _parse_value_provider(self, utterance):
        matchers = []

        for groups in re.findall("(\[regex\]\{[^}]*\})|([^\[\{]+)+", utterance):
            regex = groups[0]
            text = groups[1]

            if regex:
                match = re.search("\{([^:]+):=([^}]+)\}", regex)
                target = match.group(1)
                pattern = match.group(2)
                matchers.append((target, pattern))
            else:
                if text.strip() == "":
                    continue

                matchers.extend(text.split(' '))

        def value_provider(input):
            collected_values = {}

            current_input = input.split(' ')
            for matcher in matchers:
                if isinstance(matcher, str):
                    if len(current_input) and current_input[0].lower() == matcher.lower():
                        current_input.pop(0)
                else:
                    regex_input = " ".join(current_input)
                    target_var, regex_pattern = matcher
                    match = re.search(regex_pattern, regex_input)

                    if not match:
                        continue

                    value = match.group(0)
                    collected_values[target_var] = value

                    # remove the recognized part and continue for case multiple regexes is defined
                    regex_input = regex_input[0:match.span(0)[0]] + regex_input[match.span(0)[1]:]
                    current_input = regex_input.split(' ')

            return collected_values

        return value_provider

    def _mask_intents(self, intents):
        masked_intents = {}
        for intent, utterances in intents.items():
            masked_intents[intent] = masked_utterances = []
            for utterance in utterances:
                masked_utterance = self._mask_utterance(utterance)
                masked_utterances.append(masked_utterance)

        return masked_intents

    def _mask_utterance(self, utterance):
        return re.sub("(\[regex\]\{[^}]*\})", " something ", utterance)
