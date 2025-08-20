-- Database initialization script for Enterprise Chatbot
-- This script creates the necessary tables and indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create conversations table for storing chat history and analytics
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    user_message TEXT NOT NULL,
    bot_response TEXT NOT NULL,
    intent VARCHAR(100),
    target_product VARCHAR(100),
    confidence FLOAT DEFAULT 0.0,
    processing_time FLOAT DEFAULT 0.0,
    sources_count INTEGER DEFAULT 0,
    user_ip VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_intent ON conversations(intent);
CREATE INDEX IF NOT EXISTS idx_conversations_target_product ON conversations(target_product);
CREATE INDEX IF NOT EXISTS idx_conversations_date_intent ON conversations(DATE(created_at), intent);

-- Create user_sessions table for session management
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    page_url TEXT,
    page_title TEXT,
    product_context VARCHAR(100),
    first_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    message_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for user_sessions
CREATE INDEX IF NOT EXISTS idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity_at DESC);
CREATE INDEX IF NOT EXISTS idx_user_sessions_product_context ON user_sessions(product_context);

-- Create document_metadata table for FAISS collection metadata
CREATE TABLE IF NOT EXISTS document_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_name VARCHAR(100) NOT NULL,
    doc_id VARCHAR(255) NOT NULL,
    title TEXT,
    content_hash VARCHAR(64),
    source_file VARCHAR(255),
    metadata JSONB,
    embedding_model VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(collection_name, doc_id)
);

-- Create indexes for document_metadata
CREATE INDEX IF NOT EXISTS idx_document_metadata_collection ON document_metadata(collection_name);
CREATE INDEX IF NOT EXISTS idx_document_metadata_doc_id ON document_metadata(doc_id);
CREATE INDEX IF NOT EXISTS idx_document_metadata_content_hash ON document_metadata(content_hash);

-- Create analytics_events table for tracking user interactions
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- 'message_sent', 'response_received', 'page_view', etc.
    event_data JSONB,
    page_url TEXT,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for analytics_events
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_created_at ON analytics_events(created_at DESC);

-- Create system_metrics table for storing performance metrics
CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_type VARCHAR(50) NOT NULL, -- 'cpu', 'memory', 'disk', 'response_time', etc.
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(20), -- '%', 'ms', 'bytes', etc.
    additional_data JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for system_metrics
CREATE INDEX IF NOT EXISTS idx_system_metrics_type ON system_metrics(metric_type);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at DESC);

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_conversations_updated_at 
    BEFORE UPDATE ON conversations 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_metadata_updated_at 
    BEFORE UPDATE ON document_metadata 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Create views for common analytics queries
CREATE OR REPLACE VIEW daily_conversation_stats AS
SELECT 
    DATE(created_at) as conversation_date,
    COUNT(*) as total_conversations,
    COUNT(DISTINCT session_id) as unique_sessions,
    AVG(confidence) as avg_confidence,
    AVG(processing_time) as avg_processing_time,
    COUNT(CASE WHEN confidence >= 0.8 THEN 1 END) as high_confidence_responses
FROM conversations
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY conversation_date DESC;

-- Create view for intent performance
CREATE OR REPLACE VIEW intent_performance AS
SELECT 
    intent,
    COUNT(*) as total_queries,
    AVG(confidence) as avg_confidence,
    AVG(processing_time) as avg_processing_time,
    COUNT(CASE WHEN confidence >= 0.8 THEN 1 END) as high_confidence_count,
    MIN(created_at) as first_seen,
    MAX(created_at) as last_seen
FROM conversations
WHERE intent IS NOT NULL
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY intent
ORDER BY total_queries DESC;

-- Create view for product analytics
CREATE OR REPLACE VIEW product_analytics AS
SELECT 
    target_product,
    COUNT(*) as total_queries,
    COUNT(DISTINCT session_id) as unique_sessions,
    AVG(confidence) as avg_confidence,
    AVG(processing_time) as avg_processing_time
FROM conversations
WHERE target_product IS NOT NULL
  AND created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY target_product
ORDER BY total_queries DESC;

-- Insert some sample data for testing (optional)
-- This can be removed in production

-- Sample user session
INSERT INTO user_sessions (session_id, page_url, page_title, product_context, message_count)
VALUES 
    ('sample_session_001', 'https://example.com/products/product-a', 'Product A Features', 'product_a', 0),
    ('sample_session_002', 'https://example.com/pricing', 'Pricing Plans', NULL, 0)
ON CONFLICT (session_id) DO NOTHING;

-- Sample document metadata
INSERT INTO document_metadata (collection_name, doc_id, title, content_hash, source_file, metadata)
VALUES 
    ('product_a_features', 'doc_001', 'Product A Core Features', 'abc123', 'product_a_features.md', '{"category": "features", "version": "1.0"}'),
    ('product_a_pricing', 'doc_002', 'Product A Pricing Plans', 'def456', 'product_a_pricing.md', '{"category": "pricing", "version": "1.0"}'),
    ('warranty_support', 'doc_003', 'Warranty and Support Policy', 'ghi789', 'warranty.md', '{"category": "support", "version": "1.0"}')
ON CONFLICT (collection_name, doc_id) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chatbot_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chatbot_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO chatbot_user;

-- Create a function to clean up old data (run periodically)
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Delete conversations older than 90 days
    DELETE FROM conversations 
    WHERE created_at < CURRENT_DATE - INTERVAL '90 days';
    
    -- Delete analytics events older than 60 days
    DELETE FROM analytics_events 
    WHERE created_at < CURRENT_DATE - INTERVAL '60 days';
    
    -- Delete inactive sessions older than 30 days
    DELETE FROM user_sessions 
    WHERE last_activity_at < CURRENT_DATE - INTERVAL '30 days' 
      AND is_active = false;
      
    -- Delete system metrics older than 7 days
    DELETE FROM system_metrics 
    WHERE recorded_at < CURRENT_DATE - INTERVAL '7 days';
    
    -- Log cleanup activity
    RAISE NOTICE 'Old data cleanup completed at %', NOW();
END;
$$ LANGUAGE plpgsql;

-- Create indexes for performance optimization
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_session_created 
ON conversations(session_id, created_at DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_conversations_date_product 
ON conversations(DATE(created_at), target_product) 
WHERE target_product IS NOT NULL;

-- Enable row level security (optional, for multi-tenant scenarios)
-- ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Final optimization: analyze tables for better query planning
ANALYZE conversations;
ANALYZE user_sessions;
ANALYZE document_metadata;
ANALYZE analytics_events;
ANALYZE system_metrics;