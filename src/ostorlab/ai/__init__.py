"""Shared construction of pydantic-ai models and providers for Ostorlab agents.

Typical use::

    from ostorlab.ai import factory
    from ostorlab.ai import options
    from ostorlab.ai import settings

    model = factory.build_model(
        "openrouter/moonshotai/kimi-k2.6",
        config.OPENROUTER_API_KEY,
        options=options.ProviderOptions(litellm_gateway_url=config.LITELLM_GATEWAY_URL),
        settings=settings.default_settings(max_tokens=config.MAX_OUTPUT_TOKENS),
    )
"""
