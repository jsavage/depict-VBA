import re
import graphviz

def parse_hcs(input_text):
    entities = set()
    actions = []
    feedback = []
    nested_entities = {}

    lines = input_text.splitlines()

    for line in lines:
        line = line.strip()

        if ':' in line:
            entities_part, actions_part = line.split(':', 1)
            entities_part = entities_part.strip()
            actions_part = actions_part.strip()

            if '/' in actions_part:
                actions_list, feedback_list = actions_part.split('/', 1)
                actions_list = actions_list.strip().split()
                feedback_list = feedback_list.strip().split()
            else:
                actions_list = actions_part.split()
                feedback_list = []

            entity_list = [e for e in re.split(r'\s+', entities_part) if e != '-']

            if len(entity_list) > 2:
                raise ValueError(f"Expected exactly 2 entities before the colon, but got {entity_list}")

            controlling_entity, target_entity = map(str.strip, entity_list)
            entities.add(controlling_entity)
            entities.add(target_entity)

            for action in actions_list:
                actions.append((controlling_entity, target_entity, action))

            for fb in feedback_list:
                feedback.append((target_entity, controlling_entity, fb))

        elif '[' in line and ']' in line:
            main_entity, nested = re.match(r'(.*?)\[(.*)\]', line).groups()
            main_entity = main_entity.strip()
            nested_entities_list = nested.strip().split()

            entities.add(main_entity)
            nested_entities[main_entity] = nested_entities_list

            for ne in nested_entities_list:
                entities.add(ne)

        else:
            entity_list = [e for e in re.split(r'\s+', line) if e != '-']
            for entity in entity_list:
                entities.add(entity)

    return list(entities), actions, feedback, nested_entities

def draw_hcs(entities, actions, feedback, nested_entities, output_file):
    dot = graphviz.Digraph(format='png')

    for entity in entities:
        dot.node(entity, shape='rectangle')

    for parent, children in nested_entities.items():
        with dot.subgraph(name=f'cluster_{parent}') as sub:
            sub.attr(label=parent)
            sub.node(parent, shape='rectangle')
            for child in children:
                sub.node(child, shape='rectangle')

    for (src, tgt, action) in actions:
        dot.edge(src, tgt, label=action)
    for (src, tgt, fb) in feedback:
        dot.edge(src, tgt, label=fb, color='red')

    dot.render(output_file, cleanup=True)

def run_tests():
    test_cases = [
        {
            "input": "person microwave",
            "expected_entities": {'person', 'microwave'},
            "expected_actions": [],
            "expected_feedback": [],
            "expected_nested": {}
        },
        {
            "input": "person microwave: open close start stop",
            "expected_entities": {'person', 'microwave'},
            "expected_actions": [
                ('person', 'microwave', 'open'),
                ('person', 'microwave', 'close'),
                ('person', 'microwave', 'start'),
                ('person', 'microwave', 'stop')
            ],
            "expected_feedback": [],
            "expected_nested": {}
        },
        {
            "input": "person microwave: open close start stop / beep",
            "expected_entities": {'person', 'microwave'},
            "expected_actions": [
                ('person', 'microwave', 'open'),
                ('person', 'microwave', 'close'),
                ('person', 'microwave', 'start'),
                ('person', 'microwave', 'stop')
            ],
            "expected_feedback": [
                ('microwave', 'person', 'beep')
            ],
            "expected_nested": {}
        },
        {
            "input": "microwave [ magnetron ]\nmagnetron food: heat",
            "expected_entities": {'microwave', 'magnetron', 'food'},
            "expected_actions": [
                ('magnetron', 'food', 'heat')
            ],
            "expected_feedback": [],
            "expected_nested": {
                'microwave': ['magnetron']
            }
        },
        {
            "input": "person microwave: open close start stop / beep\nmicrowave [ magnetron ]\nmagnetron food: heat",
            "expected_entities": {'person', 'microwave', 'magnetron', 'food'},
            "expected_actions": [
                ('person', 'microwave', 'open'),
                ('person', 'microwave', 'close'),
                ('person', 'microwave', 'start'),
                ('person', 'microwave', 'stop'),
                ('magnetron', 'food', 'heat')
            ],
            "expected_feedback": [
                ('microwave', 'person', 'beep')
            ],
            "expected_nested": {
                'microwave': ['magnetron']
            }
        },
        {
            "input": "person microwave: open close start stop / beep\nmicrowave [ magnetron ]\nmagnetron food: heat\nfood warm-food -: becomes\nperson warm-food: stir / eat",
            "expected_entities": {'person', 'microwave', 'magnetron', 'food', 'warm-food'},
            "expected_actions": [
                ('person', 'microwave', 'open'),
                ('person', 'microwave', 'close'),
                ('person', 'microwave', 'start'),
                ('person', 'microwave', 'stop'),
                ('magnetron', 'food', 'heat'),
                ('food', 'warm-food', 'becomes'),
                ('person', 'warm-food', 'stir')
            ],
            "expected_feedback": [
                ('microwave', 'person', 'beep'),
                ('warm-food', 'person', 'eat')
            ],
            "expected_nested": {
                'microwave': ['magnetron']
            }
        }
    ]

    for i, case in enumerate(test_cases, 1):
        try:
            entities, actions, feedback, nested_entities = parse_hcs(case["input"])
            assert set(entities) == case["expected_entities"], f"Test Case {i} Failed: {entities} != {case['expected_entities']}"
            assert set(actions) == set(case["expected_actions"]), f"Test Case {i} Failed: {actions} != {case['expected_actions']}"
            assert set(feedback) == set(case["expected_feedback"]), f"Test Case {i} Failed: {feedback} != {case['expected_feedback']}"
            assert nested_entities == case["expected_nested"], f"Test Case {i} Failed: {nested_entities} != {case['expected_nested']}"
            print(f"Test Case {i} Passed")
        except AssertionError as e:
            print(str(e))

    print("Testing complete.")

if __name__ == "__main__":
    run_tests()
    last_case = {
        "input": "person microwave: open close start stop / beep\nmicrowave [ magnetron ]\nmagnetron food: heat\nfood warm-food -: becomes\nperson warm-food: stir / eat",
        "output_file": "hcs_diagram"
    }
    entities, actions, feedback, nested_entities = parse_hcs(last_case["input"])
    draw_hcs(entities, actions, feedback, nested_entities, last_case["output_file"])
