package com.elastic.textsearch.controller;

import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.elasticsearch.core.ElasticsearchOperations;
import org.springframework.data.elasticsearch.core.IndexOperations;
import org.springframework.data.elasticsearch.core.SearchHit;
import org.springframework.data.elasticsearch.core.SearchHits;
import org.springframework.data.elasticsearch.core.mapping.IndexCoordinates;
import org.springframework.data.elasticsearch.core.query.Criteria;
import org.springframework.data.elasticsearch.core.query.CriteriaQuery;
import org.springframework.data.elasticsearch.core.query.Query;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.server.ResponseStatusException;

import com.elastic.textsearch.entity.Product;
import com.elastic.textsearch.repository.ProductRepository;

@RestController
@RequestMapping("/products")
public class ElasticController {
	@Autowired
	public ProductRepository repository;

	@Autowired
	private ElasticsearchOperations elasticsearchOperations;

	@Value("${spring.elasticsearch.uris}")
	private String elasticsearchUri;

	@PostMapping
	public Product addProduct(@RequestBody Product product) {
		// keep existing behaviour: save to the repository's default index (annotated index)
		System.out.println(product);
		return repository.save(product);
	}

	// Save to a dynamic index. If index does not exist it will be created with mapping for Product.
	@PostMapping("/{index}")
	public Product addProductToIndex(@PathVariable String index, @RequestBody Product product) {
		if (!isValidIndexName(index)) {
			throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "Invalid index name");
		}
		IndexCoordinates coords = IndexCoordinates.of(index);
		IndexOperations indexOps = elasticsearchOperations.indexOps(coords);
		if (!indexOps.exists()) {
			indexOps.create();
			// create default mapping based on the Product class
			indexOps.putMapping(indexOps.createMapping(Product.class));
		}
		elasticsearchOperations.save(product, coords);
		return product;
	}

	// List indices visible to the configured Elasticsearch URI using the _cat API.
	@GetMapping("/indices")
	public List<String> listIndices() {
		RestTemplate rt = new RestTemplate();
		String url = elasticsearchUri;
		if (url.endsWith("/")) {
			url = url.substring(0, url.length() - 1);
		}
		String catUrl = url + "/_cat/indices?format=json";
		ResponseEntity<List> resp = rt.getForEntity(catUrl, List.class);
		List<Map<String, Object>> arr = resp.getBody();
		if (arr == null) {
			return List.of();
		}
		return arr.stream().map(m -> (String) m.get("index")).collect(Collectors.toList());
	}

	// Use a distinct path to avoid collision with the dynamic-index GET below
	@GetMapping("/name/{name}")
	public List<Product> getByName(@PathVariable String name) {
		return repository.findByName(name);
	}

	// Search by name inside a specific index
	@GetMapping("/index/{index}/name/{name}")
	public List<Product> getByNameFromIndex(@PathVariable String index, @PathVariable String name) {
	IndexCoordinates coords = IndexCoordinates.of(index);
	Query query = new CriteriaQuery(Criteria.where("name").is(name));
		SearchHits<Product> hits = elasticsearchOperations.search(query, Product.class, coords);
		return hits.stream().map(SearchHit::getContent).collect(Collectors.toList());
	}

	// Validate index name against a safe pattern for Elasticsearch index names.
	// Rules enforced here: lowercase letters, digits, dot, underscore and hyphen allowed; length 1..255; cannot start with '.'
	private boolean isValidIndexName(String index) {
		if (index == null) return false;
		if (index.length() < 1 || index.length() > 255) return false;
		if (index.charAt(0) == '.') return false;
		return index.matches("^[a-z0-9._-]+$");
	}

	@GetMapping
	public Iterable<Product> getAllProducts() {
		return repository.findAll();
	}

}
