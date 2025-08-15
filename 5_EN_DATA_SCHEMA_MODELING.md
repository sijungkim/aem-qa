### **Document 5/8: Data Model and Schema Definition**

## **💾 Data Model and Schema Definition**

This document defines the database schema used in the AEM QA System & Workstation. The system's data is stored in **MongoDB** and **ChromaDB**, with each database serving clearly distinct roles.

---

## 1. Database Overview

* **MongoDB**: Serves as the primary storage for **structured document data**, including original component data collected from AEM and translation memory (TM) at various processing stages. It forms the foundation for data version control, metadata preservation, and detailed analysis.
* **ChromaDB**: A **vector database** that stores `source_text` from the final refined translation memory converted into vectors. It handles fast and accurate semantic similarity searches based on AI.

---

## 2. MongoDB Schema

* **Database Name**: `aem_qa_system`

#### **2.1. `page_components` Collection**

The core original data collection that stores all content snapshots collected from AEM, decomposed into individual component units and stored by version.

* **Role**: Source of Truth serving as the starting point for all analysis.
* **Created by**: `src/processors/data_ingestor.py`
* **Key Fields**:
    * `_id` (ObjectId): MongoDB auto-generated unique ID.
    * `page_path` (String): AEM page path where the component belongs (e.g., `/products/sequencing/iseq-100`).
    * `version_name` (String): AEM content version name (e.g., `lm-en`, `spac-ko_KR`).
    * `version_number` (Int): System-assigned linearly increasing version number (e.g., `1`, `2`).
    * `snapshot_hash` (String): SHA256 hash of the entire page JSON. Identical hashes are considered unchanged.
    * `component_path` (String): Unique path of the component within the page (e.g., `root/:items/container/:items/text`).
    * `component_order` (Int): Rendering order of the component within the page.
    * `component_type` (String): AEM resource type (e.g., `core/wcm/components/text/v2/text`).
    * `component_content` (Object): Complete original JSON content of the component.
    * `snapshot_timestamp` (ISODate): Time when the original snapshot was collected.

#### **2.2. `clean_translation_memory_{lang_pair}` Collection**

Final translation memory that has undergone all cleaning and segmentation processes. This serves as the source data for building the AI search database (ChromaDB) for the QA workstation.

* **Role**: High-quality translation pair storage, AI training and search data source.
* **Created by**: `src/processors/ultimate_tm_builder.py`
* **Key Fields**:
    * `source_text` (String): **(Core)** Cleaned and segmented source language text.
    * `target_text` (String): **(Core)** Cleaned and segmented target language text.
    * `is_segmented` (Boolean): Whether segmented by `semantic_segmenter`.
    * `segment_index` (Int): Order of the segment if segmented (starting from 0).
    * `total_segments` (Int): Total number of segments the text was divided into.
    * `alignment_confidence` (Float): Semantic similarity score of the segmented source-target pair.
    * `quality_score` (Float): Quality score between 0.0 and 1.0 assigned by `tm_cleaner`.
    * `text_type` (String): Type of text (e.g., `title`, `sentence`, `link_text`).
    * `original_source_text` (String): Original source text before cleaning/segmentation.
    * **Inherits all** key metadata from the original component such as `page_path`, `component_path`, `version_name`, etc., allowing content traceability.

#### **2.3. `html_component_archive_{lang_pair}` Collection**

Collection that archives components excluded from `clean_translation_memory` because their translation text contains HTML tags.

* **Role**: Archiving original data of complex components containing HTML.
* **Created by**: `src/processors/ultimate_tm_builder.py`
* **Key Fields**:
    * `source_component_content` (Object): Original component JSON of the source version.
    * `target_component_content` (Object): Original component JSON of the target version.
    * `html_detection` (Object): HTML analysis information.
        * `detected_tags` (Array): List of detected HTML tags (e.g., `['p', 'strong']`).
        * `html_complexity` (String): HTML complexity (`simple`, `medium`, `complex`).
    * Inherits all original metadata such as `page_path`, `component_path`, etc.

#### **2.4. Other Collections**

* `translation_memory_{lang_pair}`: Initial TM created by `aem_tm_builder`. Intermediate output of subsequent processing.
* `untranslated_components_{lang_pair}`: List of components that couldn't form translation pairs due to different inter-version structures. `page_structure_analyzer` uses this collection to generate structure difference reports.

---

## 3. ChromaDB Schema

* **Role**: Vector index storage for fast AI-based similarity search.
* **Collection Naming**: `tm_{lang_pair}` (e.g., `tm_en_ko`, `tm_en_ja`)

Each individual item in each collection has the following structure:

* **Document**:
    * **Content**: `source_text` field from the `clean_translation_memory` collection.
    * **Role**: Original text that generates embedding vectors and serves as source text for search results.
* **Embedding**:
    * **Content**: High-dimensional vector converted from Document (`source_text`) by `SentenceTransformer` model.
    * **Role**: Used to calculate semantic distance (similarity) with other texts in vector space.
* **Metadata**:
    * **Content**: Additional information stored with vectors. Essential for enriching search results in the QA workstation.
        * `target_text` (String): **(Core)** Translation corresponding to `source_text`.
        * `page_path` (String): Original AEM page path of the translation.
        * `component_path` (String): Original component path of the translation.
    * **Role**: After finding similar `source_text`, provides users with the actual needed translation and its source information.
* **ID**:
    * **Content**: MongoDB `_id` of the `clean_translation_memory` document converted to string.
    * **Role**: Serves as a unique key connecting ChromaDB search results with original detailed data in MongoDB.