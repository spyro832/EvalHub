"""
Seed script — populates the database with sample data for development.
Run with: docker compose exec backend python -m app.scripts.seed
"""

import asyncio

from app.core.database import AsyncSessionLocal
from app.models.benchmark import Benchmark, BenchmarkItem
from app.models.model_config import ModelConfig
from app.models.prompt import Prompt
from app.models.test_suite import TestCase, TestSuite


async def seed():
    async with AsyncSessionLocal() as db:
        # Sample model configs
        ollama = ModelConfig(
            name="Llama 3.2 (Ollama)",
            provider="ollama",
            model_id="llama3.2",
            base_url="http://host.docker.internal:11434",
            is_local=True,
        )
        db.add(ollama)
        await db.flush()

        # Sample prompts
        prompts = [
            Prompt(
                name="Python Code Review",
                content="Review the following Python code and suggest improvements:\n\n{code}",
                description="General Python code review prompt",
                tags="python,code-review",
            ),
            Prompt(
                name="Explain Like I'm 5",
                content="Explain the following concept in simple terms a 5-year-old could understand: {concept}",
                description="Simplification prompt",
                tags="explanation,simplification",
            ),
            Prompt(
                name="SQL Query Optimizer",
                content="Analyze and optimize this SQL query for performance:\n\n{query}",
                description="SQL optimization prompt",
                tags="sql,optimization,database",
            ),
        ]
        for p in prompts:
            db.add(p)

        # Sample test suite
        coding_suite = TestSuite(
            name="Python Coding Benchmark",
            description="Tests for Python code generation quality",
            category="coding",
        )
        db.add(coding_suite)
        await db.flush()

        test_cases = [
            TestCase(
                suite_id=coding_suite.id,
                input="Write a Python function to check if a string is a palindrome.",
                expected_tags="python,def,return",
            ),
            TestCase(
                suite_id=coding_suite.id,
                input="Write a Python function to flatten a nested list.",
                expected_tags="python,def,list",
            ),
            TestCase(
                suite_id=coding_suite.id,
                input="Write a Python decorator that logs function execution time.",
                expected_tags="python,def,decorator",
            ),
        ]
        for tc in test_cases:
            db.add(tc)

        # ── Community Benchmarks ───────────────────────────────────────────────

        # 1. Python Coding benchmark
        coding_bench = Benchmark(
            name="Python Fundamentals",
            description="Basic Python coding tasks covering common algorithms and data structures.",
            category="coding",
            author="EvalHub Community",
        )
        db.add(coding_bench)
        await db.flush()

        coding_items = [
            BenchmarkItem(
                benchmark_id=coding_bench.id,
                input="Write a Python function to check if a number is prime.",
                expected_tags="def,return,for",
                meta={"difficulty": "easy", "topic": "math"},
            ),
            BenchmarkItem(
                benchmark_id=coding_bench.id,
                input="Write a Python function to reverse a string without using slicing.",
                expected_tags="def,return",
                meta={"difficulty": "easy", "topic": "strings"},
            ),
            BenchmarkItem(
                benchmark_id=coding_bench.id,
                input="Write a Python class for a stack with push, pop, and peek methods.",
                expected_tags="class,def,push,pop",
                meta={"difficulty": "medium", "topic": "data-structures"},
            ),
            BenchmarkItem(
                benchmark_id=coding_bench.id,
                input="Implement binary search in Python.",
                expected_tags="def,return,while",
                meta={"difficulty": "medium", "topic": "algorithms"},
            ),
            BenchmarkItem(
                benchmark_id=coding_bench.id,
                input="Write a Python generator that yields Fibonacci numbers indefinitely.",
                expected_tags="def,yield",
                meta={"difficulty": "medium", "topic": "generators"},
            ),
        ]
        for item in coding_items:
            db.add(item)

        # 2. RAG / Retrieval benchmark
        rag_bench = Benchmark(
            name="Factual Q&A",
            description="Short factual questions to test grounded response quality.",
            category="rag",
            author="EvalHub Community",
        )
        db.add(rag_bench)
        await db.flush()

        rag_items = [
            BenchmarkItem(
                benchmark_id=rag_bench.id,
                input="What is the capital of France?",
                expected_output="Paris",
                meta={"difficulty": "easy"},
            ),
            BenchmarkItem(
                benchmark_id=rag_bench.id,
                input="What does HTTP stand for?",
                expected_output="HyperText Transfer Protocol",
                meta={"difficulty": "easy"},
            ),
            BenchmarkItem(
                benchmark_id=rag_bench.id,
                input="What is the time complexity of quicksort in the average case?",
                expected_output="O(n log n)",
                meta={"difficulty": "medium"},
            ),
            BenchmarkItem(
                benchmark_id=rag_bench.id,
                input="What does SOLID stand for in software engineering?",
                expected_tags="single,open,liskov,interface,dependency",
                meta={"difficulty": "medium"},
            ),
        ]
        for item in rag_items:
            db.add(item)

        # 3. Translation benchmark
        translation_bench = Benchmark(
            name="English to Spanish Translation",
            description="Short English phrases to translate into Spanish.",
            category="translation",
            author="EvalHub Community",
        )
        db.add(translation_bench)
        await db.flush()

        translation_items = [
            BenchmarkItem(
                benchmark_id=translation_bench.id,
                input="Translate to Spanish: 'Hello, how are you?'",
                expected_output="Hola",
                meta={"source_lang": "en", "target_lang": "es"},
            ),
            BenchmarkItem(
                benchmark_id=translation_bench.id,
                input="Translate to Spanish: 'The weather is nice today.'",
                expected_output="El tiempo",
                meta={"source_lang": "en", "target_lang": "es"},
            ),
            BenchmarkItem(
                benchmark_id=translation_bench.id,
                input="Translate to Spanish: 'I would like a cup of coffee, please.'",
                expected_output="café",
                meta={"source_lang": "en", "target_lang": "es"},
            ),
        ]
        for item in translation_items:
            db.add(item)

        await db.commit()
        print("✅ Seed data created:")
        print("  - 1 model config (Ollama Llama 3.2)")
        print(f"  - {len(prompts)} prompts")
        print(f"  - 1 test suite with {len(test_cases)} test cases")
        print("  - 3 benchmarks:")
        print(f"    · Python Fundamentals ({len(coding_items)} items)")
        print(f"    · Factual Q&A ({len(rag_items)} items)")
        print(f"    · English to Spanish Translation ({len(translation_items)} items)")


if __name__ == "__main__":
    asyncio.run(seed())
