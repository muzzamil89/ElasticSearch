package com.elastic.textsearch.repository;

import java.util.List;

import org.springframework.data.elasticsearch.repository.ElasticsearchRepository;

import com.elastic.textsearch.entity.Product;

public interface ProductRepository extends ElasticsearchRepository<Product, String> {

	List<Product> findByName(String name);

}
