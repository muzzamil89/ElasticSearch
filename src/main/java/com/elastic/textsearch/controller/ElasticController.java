package com.elastic.textsearch.controller;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.elastic.textsearch.entity.Product;
import com.elastic.textsearch.repository.ProductRepository;

@RestController
@RequestMapping("/products")
public class ElasticController {
	@Autowired
	public ProductRepository repository;

	@PostMapping
	public Product addProduct(@RequestBody Product product) {
		System.out.println(product);
		return repository.save(product);
	}

	@GetMapping("/{name}")
	public List<Product> getByName(@PathVariable String name) {
		return repository.findByName(name);
	}

	@GetMapping
	public Iterable<Product> getAllProducts() {
		return repository.findAll();
	}

}
