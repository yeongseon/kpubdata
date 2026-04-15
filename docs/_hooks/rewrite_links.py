LINK_REPLACEMENTS = [
    ("./docs/product-family-architecture.md", "product-family-architecture.md"),
    ("./docs/architecture-diagrams.md", "architecture-diagrams.md"),
    ("./docs/datago-api-reference.md", "datago-api-reference.md"),
    ("./docs/quickstart.md", "quickstart.md"),
    ("./docs/adrs/", "adrs/index.md"),
    ("../../SUPPORTED_DATA.md", "../supported-data.md"),
    ("../PROVIDER_ADAPTER_CONTRACT.md", "provider-adapter-contract.md"),
    ("../CANONICAL_MODEL.md", "canonical-model.md"),
    ("../CONTRIBUTING.md", "contributing.md"),
    ("../ARCHITECTURE.md", "architecture.md"),
    ("../AGENTS.md", "agents.md"),
    ("../API_SPEC.md", "api-spec.md"),
    ("../README.md", "index.md"),
    ("./PROVIDER_ADAPTER_CONTRACT.md", "provider-adapter-contract.md"),
    ("./CANONICAL_MODEL.md", "canonical-model.md"),
    ("./CONTRIBUTING.md", "contributing.md"),
    ("./ARCHITECTURE.md", "architecture.md"),
    ("./SUPPORTED_DATA.md", "supported-data.md"),
    ("./VALIDATION.md", "validation.md"),
    ("./CHANGELOG.md", "changelog.md"),
    ("./PACKAGING.md", "packaging.md"),
    ("./ROADMAP.md", "roadmap.md"),
    ("./API_SPEC.md", "api-spec.md"),
    ("./README.md", "index.md"),
    ("./AGENTS.md", "agents.md"),
    ("./PRD.md", "prd.md"),
    ("](./providers/)", "](providers/index.md)"),
    ("](adrs/)", "](adrs/index.md)"),
]


def on_page_markdown(markdown: str, page: object, config: object, files: object) -> str:
    _ = (page, config, files)
    for source, target in LINK_REPLACEMENTS:
        markdown = markdown.replace(source, target)
    return markdown
