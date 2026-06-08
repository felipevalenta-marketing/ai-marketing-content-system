# AI Marketing Content System

## Knowledge-Driven AI Marketing Platform

An AI-powered multi-tenant content generation platform that combines GPT-4o, organizational knowledge bases, brand guidelines and contextual business intelligence to generate highly relevant marketing content across multiple marketing channels.

---

# Project Overview

Traditional AI tools generate content using only the user prompt, often producing generic outputs that lack brand consistency, audience relevance and business alignment.

The AI Marketing Content System introduces a knowledge-driven architecture where every request is enriched with contextual business information before reaching the AI model.

The platform combines:

- Brand Guidelines
- Audience Profiles
- Business Objectives
- Organizational Context
- Property Information
- Prompt Orchestration
- GPT-4o Reasoning

to generate highly relevant and brand-aligned marketing content.

---

# Problem Statement

Marketing teams frequently face challenges such as:

- Generic AI-generated content
- Inconsistent brand messaging
- Poor audience targeting
- Lack of contextual business understanding
- Time-consuming content creation workflows

This project solves these issues through contextual knowledge injection and AI workflow orchestration.

---

# Solution

The platform enriches every content generation request with organizational knowledge before sending it to GPT-4o.

This produces:

- More relevant content
- Better audience targeting
- Consistent brand messaging
- Multi-channel content generation
- Reduced manual editing

---

# Key Features

## Multi-Tenant Architecture

Supports multiple:

- Organizations
- Teams
- Workspaces
- Brands

while maintaining data isolation.

---

## Contextual Knowledge Injection

Every request is enriched using:

- Brand Guidelines
- Audience Profiles
- Business Objectives
- Property Information
- Organizational Context

before content generation.

---

## GPT-4o Content Generation

Generates:

- Instagram Posts
- Facebook Posts
- LinkedIn Content
- Property Descriptions
- Video Scripts
- Image Prompts
- Ad Copy

---

## Prompt Orchestration Engine

Builds structured prompts dynamically based on:

- User request
- Business context
- Brand requirements
- Audience intelligence

---

# Architecture Overview

```text
User Request
      │
      ▼
Knowledge Sources
      │
      ▼
Context Enrichment
      │
      ▼
Prompt Orchestration
      │
      ▼
GPT-4o
      │
      ▼
Structured Marketing Content
```

---

# Content Generation Pipeline

## Step 1 – Prompt Submission

User submits a content request containing:

- Property Details
- Marketing Objective
- Audience Information
- Platform Selection

---

## Step 2 – Knowledge Enrichment

The system retrieves:

- Brand Guidelines
- Audience Profiles
- Property Information
- Business Objectives

---

## Step 3 – Prompt Orchestration

The context is merged into a structured prompt optimized for GPT-4o.

---

## Step 4 – Content Generation

GPT-4o generates contextual marketing content.

---

## Step 5 – Delivery

Structured outputs are returned for:

- Instagram
- Facebook
- LinkedIn
- Ad Copy
- Property Listings
- Video Scripts

---

# Knowledge Sources

The platform uses five contextual layers:

## 1. Brand Guidelines

Defines:

- Voice
- Tone
- Messaging Style
- Content Standards

---

## 2. Property Information

Includes:

- Location
- Amenities
- Pricing
- Property Features
- Selling Points

---

## 3. Audience Profiles

Contains:

- Buyer Personas
- Customer Segments
- Audience Preferences

---

## 4. Business Objectives

Supports goals such as:

- Lead Generation
- Awareness
- Engagement
- Conversion

---

## 5. Organizational Context

Provides:

- Workspace Configuration
- Team Settings
- Organization Information

---

# Uniqueness Demonstration

## Generic AI vs Knowledge-Driven AI

| Feature | Generic AI | AI Marketing Content System |
|----------|------------|----------------------------|
| Brand Alignment | ❌ | ✅ |
| Audience Awareness | ❌ | ✅ |
| Business Objectives | ❌ | ✅ |
| Organizational Context | ❌ | ✅ |
| Knowledge Sources | ❌ | ✅ |
| Multi-Channel Outputs | Limited | ✅ |
| Structured Delivery | ❌ | ✅ |

---

# Generated Content Examples

The platform can generate:

## Instagram & Facebook Posts

- Hook
- Caption
- CTA
- Hashtags

---

## LinkedIn Content

- Professional Copy
- CTA
- Engagement Optimization

---

## Video Scripts

- Hook
- Scene Structure
- CTA

---

## Property Descriptions

- Highlights
- Benefits
- Audience Positioning
- CTA

---

# Technical Architecture

## Frontend

Built using:

- React 18
- TypeScript
- Vite

Features:

- Responsive SaaS Dashboard
- Content Studio
- Workspace Management
- Multi-Tenant Interface

---

## Backend

Built using:

- Python
- FastAPI

Responsibilities:

- API Management
- Workflow Orchestration
- Content Generation
- Validation

---

## AI Layer

Powered by:

- GPT-4o
- Prompt Engineering
- Context Injection

---

## Knowledge Layer

Includes:

- Brand Guidelines
- Audience Profiles
- Property Information
- Business Objectives

---

## Storage

Stores:

- JSON Knowledge Bases
- Generated Assets
- Configuration Files

---

## Infrastructure

Built with:

- Docker
- Docker Compose

---

# Project Structure

```text
ai-marketing-content-system/
│
├── frontend/
├── fastapi/
├── scripts/
├── templates/
├── outputs/
├── tests/
├── screenshots/
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── PROJECT_REQUIREMENTS.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/felipevalenta-marketing/ai-marketing-content-system.git
cd ai-marketing-content-system
```

---

## Backend Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

---

## Run API

```bash
uvicorn src.api.main:app --reload
```

---

# Environment Variables

Create a `.env` file:

```env
OPENAI_API_KEY=your_api_key_here
```

---

# Docker Deployment

```bash
docker compose up --build
```

---

# Agile Project Management

The project was developed using an agile Kanban workflow.

Required checkpoints:

- Planning Board
- Midpoint Board
- Final Board

Development was tracked through:

- Scope Definition
- Feature Prioritization
- Sprint Execution
- Acceptance Validation

---

# Deliverables

## GitHub Repository

- Organized project structure
- Version control history
- Documentation

---

## Product Demonstration

Demonstrates:

- Knowledge Base Integration
- Prompt Orchestration
- GPT-4o Content Generation
- Structured Outputs

---

## Uniqueness Validation

Shows the difference between:

- Generic AI Outputs
- Context-Enriched AI Outputs

---

## Technical Implementation

Includes:

- Multi-Tenant Architecture
- Context Injection
- Prompt Engineering
- GPT-4o Integration
- API Development

---

# Future Improvements

Planned enhancements:

- Vector Database Integration
- Full RAG Architecture
- Semantic Search
- CRM Integrations
- Analytics Dashboard
- Automated Campaign Scheduling

---

# Author

Carlos Felipe Valencia

Ironhack AI Engineering Bootcamp

Final Project – AI Marketing Content System

2026

---

# License

This project was developed for educational purposes as part of the Ironhack AI Engineering Bootcamp Final Project.
