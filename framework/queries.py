# TODO

g.update(
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX error_foaf: <http://xmlns.com/foaf/0.1/ERROR/>
        PREFIX ex: <http://example.org/people/>
        DELETE {
            ex:Linda a ?o .
        }
        INSERT { 
            ex:Linda1 a ?o . 
        }
        WHERE {
            ex:Linda a ?o .
        }
        """
    )


g.update(
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX error_foaf: <http://xmlns.com/foaf/0.1/ERROR/>
        DELETE { 
            ?s foaf:knows ?o . 
        }
        INSERT { 
            ?s error_foaf:knows ?o . 
        }
        WHERE {
            ?s foaf:knows ?o .
        }
        """
    )

g.update(
        """
        PREFIX foaf: <http://xmlns.com/foaf/0.1/>
        PREFIX error_foaf: <http://xmlns.com/foaf/0.1/ERROR/>
        DELETE {
            ?s a foaf:Person .
        }
        INSERT { 
            ?s a error_foaf:Human . 
        }
        WHERE {
            ?s a foaf:Person .
        }
        """
    )

'''q = prepareUpdate(
    "INSERT DATA { <?person1> foaf:knows <?person2> .}",
    initNs = { "foaf": FOAF }
)

tim = rdflib.URIRef("http://www.w3.org/People/Berners-Lee/card#i")
g.update(q, initBindings={'person1': tim, 'person2': bob})