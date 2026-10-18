<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import Form from "$lib/ui/form/Form.svelte";
  import EmailField from "$lib/ui/form/EmailField.svelte";
  import Button from "$lib/ui/Button.svelte";
  import { api } from "$lib/api/index";
  import { authView } from "$lib/app";

  let email: string = "";
  let errorMessage: string = "";
  let successMessage: string = "";
  let isLoading: boolean = false;

  const handleSubmit = async () => {
    errorMessage = "";
    successMessage = "";

    if (!email) {
      errorMessage = m.forgot_email_required();
      return;
    }

    isLoading = true;

    try {
      await api.auth.forgotPassword(email);
      successMessage = m.forgot_sent();
    } catch (error: any) {
      errorMessage = error.message || m.forgot_failed();
    } finally {
      isLoading = false;
    }
  };
</script>

<Form title={m.forgot_title()} {errorMessage} submitHandler={handleSubmit}>
  <p class="hint">{m.forgot_hint()}</p>
  <EmailField bind:value={email} />
  <Button type="submit" disabled={isLoading}>{isLoading ? m.forgot_submitting() : m.forgot_submit()}</Button>
  {#if successMessage}
    <p class="success">{successMessage}</p>
  {/if}
  <p class="login-link">
    <button type="button" class="link-button" onclick={() => authView.set("login")}>
      {m.auth_back_to_login()}
    </button>
  </p>
</Form>

<style>
  .hint {
    margin: 0;
    font-size: 0.9rem;
  }

  .success {
    color: var(--color-success);
    text-align: center;
    margin: 0;
  }

  .login-link {
    text-align: center;
    margin-top: 1rem;
    font-size: 0.9rem;
  }

  .link-button {
    background: none;
    border: none;
    padding: 0;
    font: inherit;
    color: var(--color-primary);
    text-decoration: underline;
    cursor: pointer;
  }
</style>
