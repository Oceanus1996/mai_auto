"""Thin calls into upstream implementations. No research prompts live here."""
import asyncio
import importlib
import importlib.util
import inspect
from pathlib import Path
import sys
from .transport import ModelTransport


def arbor_module(source):
    """Map upstream's src package to its declared installed package name, arbor."""
    spec = importlib.util.spec_from_file_location('arbor', source / 'src/__init__.py',
                    submodule_search_locations=[str(source / 'src')])
    module = importlib.util.module_from_spec(spec)
    sys.modules['arbor'] = module
    spec.loader.exec_module(module)
    return importlib.import_module('arbor.coordinator.idea_tree')


def call(adapter, source, payload, output, model=None):
    source, output = Path(source), Path(output)
    sys.path.insert(0, str(source))
    if adapter == 'arbor_tree':
        native = arbor_module(source)
        tree_path = output / 'idea_tree.json'
        tree = native.IdeaTree.load_json(tree_path) if tree_path.exists() else native.IdeaTree(
            root=native.Node(id='ROOT', parent_id=None, hypothesis=payload['topic']),
            json_path=tree_path, md_path=output / 'idea_tree.md')
        for entry in payload.get('nodes', []):
            parent = tree.get_node(entry['parent_id'])
            if parent is None:
                raise ValueError('Parent must exist')
            tree.add_node(native.Node(id=entry['id'], parent_id=parent.id,
                depth=parent.depth + 1, hypothesis=entry['hypothesis'],
                grounding=entry.get('grounding', '')))
        tree.save()
        return {'tree_file': str(tree_path), 'nodes': [n.to_dict() for n in tree.get_all_nodes()]}
    llm = ModelTransport(**model) if model else None
    if adapter == 'claw_debate':
        from researchclaw.pipeline.debate import run_debate
        from researchclaw.prompts import PromptManager
        if llm is None:
            raise ValueError('Model configuration required')
        prompts = PromptManager()
        text, record = run_debate(panel=[llm], judge=llm,
            roles=prompts.debate_roles_hypothesis(), variables=payload['variables'],
            rounds=payload.get('rounds', 1), synth_prompt='hypothesis_synthesize',
            out_dir=output / 'debate', prompts=prompts, author_model=model['model'])
        return {'text': text, 'record': record, 'model_independence': False}
    if adapter in ('coi_review', 'coi_chain'):
        from agents import DeepResearchAgent, ReviewAgent
        if llm is None:
            raise ValueError('Model configuration required')
        researcher = DeepResearchAgent(save_file=str(output / 'coi'), llm=llm, cheap_llm=llm,
                                       **payload.get('settings', {}))
        if adapter == 'coi_chain':
            result = researcher.generate_idea_with_chain(**payload['arguments'])
        else:
            reviewer = ReviewAgent(save_file=str(output / 'coi_review'), llm=llm, cheap_llm=llm)
            result = researcher.improve_experiment(review_agent=reviewer, **payload['arguments'])
        return asyncio.run(result)
    raise ValueError(f'Adapter not implemented: {adapter}; no replacement method will be used')
