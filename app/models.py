from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey, Text, JSON, Enum, Numeric
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base

class SubscriptionTier(enum.Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    google_id = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    # Relationships
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_keys = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    user_agents = relationship("UserAgent", back_populates="user", cascade="all, delete-orphan")

class Subscription(Base):
    __tablename__ = "subscriptions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tier = Column(String, default=SubscriptionTier.BASIC.value)
    stripe_customer_id = Column(String, unique=True, nullable=True)
    stripe_subscription_id = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    auto_renew = Column(Boolean, default=True)
    payment_method_id = Column(String, nullable=True)
    billing_email = Column(String, nullable=True)
    subscription_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    usage = relationship("AgentUsage", back_populates="subscription", cascade="all, delete-orphan")

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    last_used = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")

class UserAgent(Base):
    __tablename__ = "user_agents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(String, nullable=False)  # e.g., "portfolio_agent", "options_strategy_agent"
    is_enabled = Column(Boolean, default=True)
    custom_settings = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="user_agents")
    usage = relationship("AgentUsage", back_populates="user_agent", cascade="all, delete-orphan")

class AgentUsage(Base):
    __tablename__ = "agent_usage"
    id = Column(Integer, primary_key=True, index=True)
    user_agent_id = Column(Integer, ForeignKey("user_agents.id"))
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"))
    request_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)
    last_used = Column(DateTime, default=datetime.utcnow)
    month = Column(Integer, nullable=False)  # 1-12
    year = Column(Integer, nullable=False)
    
    # Relationships
    user_agent = relationship("UserAgent", back_populates="usage")
    subscription = relationship("Subscription", back_populates="usage")

class PortfolioRecord(Base):
    __tablename__ = "portfolio_records"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data = Column(JSON, nullable=False)  # JSON containing positions, etc.
    is_public = Column(Boolean, default=False)

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    agent_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    result_type = Column(String, nullable=False)  # e.g., "portfolio_analysis", "options_strategy"
    input_data = Column(JSON, nullable=True)
    result_data = Column(JSON, nullable=False)
    is_saved = Column(Boolean, default=False)
    name = Column(String, nullable=True)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    task_type = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, running, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    params = Column(JSON, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)

class AgentListing(Base):
    __tablename__ = "agent_listings"
    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic Information
    name = Column(String(255), nullable=False, index=True)
    short_description = Column(String(500), nullable=False)
    detailed_description = Column(Text, nullable=True)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True)
    tags = Column(JSON, nullable=True)  # Array of strings
    
    # Technical Specifications
    model_architecture = Column(String(100), nullable=True)
    supported_languages = Column(JSON, nullable=True)  # Array of language codes
    api_documentation = Column(Text, nullable=True)
    technical_requirements = Column(JSON, nullable=True)
    integration_complexity = Column(String(20), nullable=True)  # easy, medium, complex
    
    # Pricing
    pricing_model = Column(String(20), nullable=False)
    base_price = Column(Numeric(10, 2), nullable=True)
    subscription_price = Column(Numeric(10, 2), nullable=True)
    per_use_price = Column(Numeric(10, 4), nullable=True)
    custom_pricing_available = Column(Boolean, default=False)
    free_trial_available = Column(Boolean, default=False)
    free_trial_duration = Column(Integer, nullable=True)  # days
    free_usage_limit = Column(Integer, nullable=True)  # requests/calls
    
    # Media and Demo
    logo_url = Column(String(500), nullable=True)
    screenshot_urls = Column(JSON, nullable=True)  # Array of URLs
    video_demo_url = Column(String(500), nullable=True)
    demo_api_endpoint = Column(String(500), nullable=True)
    
    # Performance Metrics
    accuracy_score = Column(Float, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    uptime_percentage = Column(Float, nullable=True)
    scalability_rating = Column(Integer, nullable=True)  # 1-5
    
    # Status and Verification
    status = Column(String(20), default="draft")
    is_verified = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    is_trending = Column(Boolean, default=False)
    verification_level = Column(String(20), nullable=True)  # basic, advanced, enterprise
    
    # SEO and Discovery
    slug = Column(String(255), unique=True, nullable=True, index=True)
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(String(500), nullable=True)
    search_keywords = Column(JSON, nullable=True)
    
    # Analytics
    view_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    rating_average = Column(Float, nullable=True)
    rating_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    
    # Relationships
    seller = relationship("User", foreign_keys=[seller_id])
    pricing_tiers = relationship("AgentPricingTier", back_populates="agent", cascade="all, delete-orphan")
    reviews = relationship("AgentReview", back_populates="agent", cascade="all, delete-orphan")
    purchases = relationship("AgentPurchase", back_populates="agent")
    analytics = relationship("AgentAnalytics", back_populates="agent", cascade="all, delete-orphan")

class AgentPricingTier(Base):
    __tablename__ = "agent_pricing_tiers"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent_listings.id"), nullable=False)
    
    name = Column(String(100), nullable=False)  # Basic, Pro, Enterprise
    description = Column(Text, nullable=True)
    price = Column(Numeric(10, 2), nullable=False)
    billing_cycle = Column(String(20), nullable=True)  # monthly, yearly, one_time
    features = Column(JSON, nullable=True)  # Array of feature descriptions
    usage_limits = Column(JSON, nullable=True)  # API calls, tokens, etc.
    support_level = Column(String(20), nullable=True)
    is_popular = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("AgentListing", back_populates="pricing_tiers")

class AgentPurchase(Base):
    __tablename__ = "agent_purchases"
    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agent_listings.id"), nullable=False)
    pricing_tier_id = Column(Integer, ForeignKey("agent_pricing_tiers.id"), nullable=True)
    
    # Transaction Details
    transaction_id = Column(String(100), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    payment_method = Column(String(50), nullable=True)
    status = Column(String(20), default="pending")
    
    # Stripe/Payment Integration
    stripe_payment_intent_id = Column(String(255), nullable=True)
    stripe_customer_id = Column(String(255), nullable=True)
    
    # License and Access
    license_key = Column(String(255), unique=True, nullable=True)
    api_key = Column(String(255), unique=True, nullable=True)
    access_url = Column(String(500), nullable=True)
    expires_at = Column(DateTime, nullable=True)
    usage_remaining = Column(Integer, nullable=True)
    
    # Metadata
    purchase_metadata = Column(JSON, nullable=True)
    refund_reason = Column(Text, nullable=True)
    refunded_at = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    buyer = relationship("User", foreign_keys=[buyer_id])
    agent = relationship("AgentListing", back_populates="purchases")
    pricing_tier = relationship("AgentPricingTier")
    reviews = relationship("AgentReview", back_populates="purchase")

class AgentReview(Base):
    __tablename__ = "agent_reviews"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent_listings.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    purchase_id = Column(Integer, ForeignKey("agent_purchases.id"), nullable=False)
    
    # Review Content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    pros = Column(JSON, nullable=True)  # Array of strings
    cons = Column(JSON, nullable=True)  # Array of strings
    
    # Detailed Ratings
    ease_of_use = Column(Integer, nullable=True)  # 1-5
    performance = Column(Integer, nullable=True)  # 1-5
    documentation_quality = Column(Integer, nullable=True)  # 1-5
    customer_support = Column(Integer, nullable=True)  # 1-5
    value_for_money = Column(Integer, nullable=True)  # 1-5
    
    # Moderation
    is_verified_purchase = Column(Boolean, default=True)
    is_moderated = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    helpful_votes = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    agent = relationship("AgentListing", back_populates="reviews")
    reviewer = relationship("User", foreign_keys=[reviewer_id])
    purchase = relationship("AgentPurchase", back_populates="reviews")

class AgentAnalytics(Base):
    __tablename__ = "agent_analytics"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agent_listings.id"), nullable=False)
    
    # Time Period
    date = Column(DateTime, nullable=False, index=True)
    period_type = Column(String(10), nullable=False)  # daily, weekly, monthly
    
    # Metrics
    views = Column(Integer, default=0)
    unique_visitors = Column(Integer, default=0)
    demo_requests = Column(Integer, default=0)
    purchases = Column(Integer, default=0)
    revenue = Column(Numeric(10, 2), default=0)
    conversion_rate = Column(Float, nullable=True)
    
    # Geographic Data
    top_countries = Column(JSON, nullable=True)
    top_referrers = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    agent = relationship("AgentListing", back_populates="analytics")

class AgentWishlist(Base):
    __tablename__ = "agent_wishlists"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("agent_listings.id"), nullable=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    agent = relationship("AgentListing") 