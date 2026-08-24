from app.utils.sql_cleaner import clean_sql
from app.validator.sql_ast_validator import validate_sql, SQLValidationError
from app.llm.sql_generator import generate_sql

def test_empty_sql_handling():
    print("=" * 70)
    print("TESTING EMPTY SQL & NONETYPE HANDLERS")
    print("=" * 70)

    # 1. Test clean_sql with leading semicolons and empty inputs
    test1 = ";;; ```sql ; SELECT u.id, u.name FROM users u; ```"
    cleaned1 = clean_sql(test1)
    print("Clean 1 Output:", cleaned1)
    assert cleaned1 == "SELECT u.id, u.name FROM users AS u LIMIT 100", f"Unexpected: {cleaned1}"

    test2 = "; ; ;"
    cleaned2 = clean_sql(test2)
    print("Clean 2 Output:", repr(cleaned2))
    assert cleaned2 == "", f"Expected empty string, got: {cleaned2}"

    # 2. Test validate_sql null check
    empty_caught = False
    try:
        validate_sql("")
    except SQLValidationError as e:
        empty_caught = True
        print("AST Null Check Caught Expected Error:", str(e))
    assert empty_caught, "validate_sql failed to catch empty string!"

    # 3. Test generate_sql fallback logic
    prompt = "Table `users` with columns: [id, name, user_role]\nBusiness Question: Show all retailers"
    gen_sql = generate_sql(prompt)
    print("Generate SQL Output:", gen_sql)
    assert gen_sql and "SELECT" in gen_sql, "generate_sql failed to return valid SQL!"

    print("\nALL EMPTY SQL & NONETYPE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_empty_sql_handling()
